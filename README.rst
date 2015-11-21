Test web app showcasing ``aiohttp.web``, ``aiohttp_jinja2`` & ``aiopg`` usage

Dependencies
------------
- Python >= 3.5.x
- aiohttp >= 0.18.x
- aiopg >= 0.7.x
- aiohttp_jinja2 >= 0.6.x
- Postgres >= 9.2.x

Usage
-----
Serve the app using::

  python3.5 app.py $STATIC_DIR $TEMPLATE_DIR $HOST_IP $HOST_PORT $POSTGRES_DSN
