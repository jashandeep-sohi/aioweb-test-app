// vim: filetype=javascript tabstop=2 expandtab

function setInputAttrs(inputs) {
  var inputs = inputs.prop("required", true);
  
  inputs.filter("[name=firstname]").prop("placeholder", "First Name");
  inputs.filter("[name=lastname]").prop("placeholder", "Last Name");
  inputs.filter("[name=dob]").prop({
    "placeholder": "Date of Birth (YYYY-MM-DD)",
    "pattern": "\\d{4}-\\d{2}-\\d{2}"
  });
  inputs.filter("[name=zipcode]").prop({
    "placeholder": "Zip Code (xxxxx)",
    "pattern": "\\d{5}"
  });
}

function serializeForm(form) {
  return JSON.stringify(form.serializeArray().reduce(function(o, elm) {
    o[elm.name] = elm.value;
    return o
  }, {}));
}

function onUserAdd(event) {
  var button = $(event.target);
  var form = $(event.target.form);
  
  if (!form[0].checkValidity()) {
    $('<input type="submit">').hide().appendTo(form).click().remove();
    return false;
  }
  
  button.prop("disabled", true);
  json = serializeForm(form);
  
  $.ajax({
    method: "POST",
    url: "/api/users",
    contentType: "application/json; charset=UTF-8",
    data: json
  }).done(function(data, status) {
    console.log(status);
    button.toggleClass("action-failed", false);
  }).fail(function(xhr, status) {
    console.log(status);
    button.toggleClass("action-failed", true);
  }).always(function() {
    button.prop("disabled", false);
  });
}

function onUserUpdate(event) {
  var button = $(event.target);
  var form = $(event.target.form);
  
  if (!form[0].checkValidity()) {
    $('<input type="submit">').hide().appendTo(form).click().remove();
    return false;
  }
  
  button.prop("disabled", true);
  json = serializeForm(form);
  
  $.ajax({
    method: "PUT",
    url: "/api/users",
    contentType: "application/json; charset=UTF-8",
    data: json
  }).done(function(data, status) {
    console.log(status);
    button.toggleClass("action-failed", false);
  }).fail(function(xhr, status) {
    console.log(status);
    button.toggleClass("action-failed", true);
  }).always(function() {
    button.prop("disabled", false);
  });
}

function onUserRemove(event) {
  var button = $(event.target);
  var form = $(event.target.form);
  var id = form[0].elements["id"].value;
  
  button.prop("disabled", true);
  
  $.ajax({
    method: "DELETE",
    url: "/api/users",
    contentType: "application/json; charset=UTF-8",
    data: JSON.stringify({"id": id})
  }).done(function(data, status) {
    console.log(status);
    form.remove();
  }).fail(function(xhr, status) {
    console.log(status);
    button.toggleClass("action-failed", true);
  });
}
  
function createUserForm(user) {    
  var form = $("<form>").append($("<input>").prop({
    "type": "hidden",
    "name": "id",
    "value": user.id
  }));
  
  [
    "firstname",
    "lastname",
    "dob",
    "zipcode"
  ].forEach(function(name) {
    form.append($("<input>").prop({
      "type": "text",
      "name": name,
      "value": user[name]
    }));
  });
  
  form.append($(
    '<button name="update" type="button">Update</button>' +
    '<button name="remove" type="button">Remove</button>'
  ));
  
  setInputAttrs(form.filter("input:not([name=id])"));
  
  return form;
}

function onLoadMore(event) {
  var button = $(event.target);
  button.prop("disabled", true);
  
  $.ajax({
    method: "GET",
    url: "/api/users",
    contentType: false,
    data: {
      limit: 10,
      offset: $("div#user-entries>form").length
    },
    dataType: "json"
  }).done(function(data, status) {
    console.log(status);
    button.toggleClass("action-failed", false);
    
    if (data.length > 0) {
      var user_entries = $("div#user-entries");
              
      var new_entries = $(data.map(createUserForm)).map(function() {
        return this.toArray();
      });
      
      new_entries.find("button[name=update]").click(onUserUpdate);
      new_entries.find("button[name=remove]").click(onUserRemove);
      user_entries.append(new_entries);
    }
  }).fail(function(xhr, status) {
    console.log(status);
    button.toggleClass("action-failed", true);
  }).always(function() {
    button.prop("disabled", false);
  });
}

$("section#add>form>button[name=add]").click(onUserAdd);
$("div#user-entries>form>button[name=update]").click(onUserUpdate);
$("div#user-entries>form>button[name=remove]").click(onUserRemove);
$("section#exisiting>button[name=more]").click(onLoadMore);

setInputAttrs($("input:not([name=id])"));
