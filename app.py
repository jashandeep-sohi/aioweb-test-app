# vim: filetype=python3 tabstop=2 expandtab

import asyncio as aio
import aiohttp.web as aioweb
import aiohttp_jinja2 as aiojinja2
import jinja2
import aiopg
import argparse
import signal
import json

@aiojinja2.template("index.html")
async def index(req):
  users = json.loads(
    await req.app["users"].read({"offset": "0", "limit": "10"})
  )
  
  return {"title": "Test App", "heading": "Users", "users": users}

class Users(object):
  """
  Users DB model
  """

  def __init__(self, pool):
    self.pool = pool
  
  @classmethod
  async def init(cls, pool):
    with await pool.cursor() as cur:
      await cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
          id serial PRIMARY KEY,
          created timestamp with time zone DEFAULT clock_timestamp(),
          firstname text NOT NULL CHECK (firstname <> ''),
          lastname text NOT NULL CHECK (lastname <> ''),
          dob date,
          zipcode integer
        )
        """
      )
      
    return cls(pool)
    
  async def create(self, params):
    with await self.pool.cursor() as cur:
      await cur.execute(
        """
        INSERT INTO users (firstname, lastname, dob, zipcode)
        VALUES (%(firstname)s, %(lastname)s, %(dob)s, %(zipcode)s)
        """,
        params
      )
  
  async def read(self, params):
    with await self.pool.cursor() as cur:
      await cur.execute(
        """
        SELECT coalesce(
          array_to_json(array_agg(row_to_json(t, true)), true)::text, '[]'
        )
        FROM (
          SELECT id, firstname, lastname, dob, zipcode
          FROM users
          ORDER BY created
          LIMIT %(limit)s
          OFFSET %(offset)s
        ) as t
        """,
        params
      )
      json = (await cur.fetchone())[0]
    
    return json
  
  async def update(self, params):
    with await self.pool.cursor() as cur:
      await cur.execute(
        """
        UPDATE users SET
          firstname = %(firstname)s,
          lastname = %(lastname)s,
          dob = %(dob)s,
          zipcode = %(zipcode)s
        WHERE id = %(id)s
        """,
        params
      )
      return cur.rowcount
  
  async def delete(self, params):
    with await self.pool.cursor() as cur:
      await cur.execute(
        """
        DELETE FROM users WHERE id = %(id)s
        """,
        params
      )
  

class UsersView(object):
  """
  Users DB handlers
  """
  def __init__(self, users):
    self.users = users
    
  async def create(self, req):
    params = await req.json()
    
    if not params.keys() & {"firstname", "lastname", "dob", "zipcode"}:
      return aioweb.HTTPBadRequest(text = "invalid JSON")
    
    try:
      await self.users.create(params)
    except Exception:
      return aioweb.HTTPBadRequest()
      
    return aioweb.HTTPNoContent()
  
  async def read(self, req):
    params = req.GET
    
    query_params = {
      "limit": "10",
      "offset": "0",
    }
    query_params.update(params)
    
    try:
      json = await self.users.read(query_params)
    except Exception:
      return aioweb.HTTPBadRequest()
      
    return aioweb.Response(text = json, content_type = "application/json")
  
  async def update(self, req):
    params = await req.json()
    
    if not params.keys() & {"id", "firstname", "lastname", "dob", "zipcode"}:
      return aioweb.HTTPBadRequest(text = "invalid JSON")
    
    try:
      count = await self.users.update(params)
    except Exception:
      return aioweb.HTTPBadRequest()
    
    if not count:
      return aioweb.HTTPBadRequest()
    
    return aioweb.HTTPNoContent()
    
  async def delete(self, req):
    params = await req.json()
    
    if "id" not in params:
      return aioweb.HTTPBadRequest(text = "invalid JSON")
    
    try:
      await self.users.delete(params)
    except Exception:
      return aioweb.HTTPBadRequest()
    
    return aioweb.HTTPNoContent()

async def main(loop, args):
  pg_pool = await aiopg.create_pool(args.dsn, enable_hstore = False)
  users = await Users.init(pg_pool)
  
  app = aioweb.Application()
  aiojinja2.setup(app, loader = jinja2.FileSystemLoader(args.templates))
  app["users"] = users
  
  router = app.router
  
  #Routes
  router.add_route("GET", "/", index)
  router.add_static("/static", args.static)
  
  users_view = UsersView(users)
  router.add_route("POST", "/api/users", users_view.create)
  router.add_route("GET", "/api/users", users_view.read)
  router.add_route("PUT", "/api/users", users_view.update)
  router.add_route("DELETE", "/api/users", users_view.delete)
  
  handler = app.make_handler()
  server = await loop.create_server(handler, args.host, args.port)
  for sock in server.sockets:
    print("Serving on", sock.getsockname())
  
  close_fut = aio.Future()
  loop.add_signal_handler(signal.SIGINT, close_fut.set_result, None)
  await close_fut
  loop.remove_signal_handler(signal.SIGINT)
  
  print("Closing...")
  
  await handler.finish_connections(1.0)
  server.close()
  await server.wait_closed()
  await app.finish()
  pg_pool.close()
  await pg_pool.wait_closed()

if __name__ == "__main__":
  arg_parser = argparse.ArgumentParser(
    description = "test web app"
  )
  
  arg_parser.add_argument(
    "static",
    help = "static files dir",
  )
  arg_parser.add_argument(
    "templates",
    help = "jinja2 templates dir",
  )
  arg_parser.add_argument(
    "host",
    help = "TCP/IP hostname to serve on",
  )
  arg_parser.add_argument(
    "port",
    help = "TCP/IP port to serve on",
  )
  arg_parser.add_argument(
    "dsn",
    help = "postgres database connection string",
  )
  
  args = arg_parser.parse_args()
  
  loop = aio.get_event_loop()
  loop.run_until_complete(main(loop, args))
  loop.close()
