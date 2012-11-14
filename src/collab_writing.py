# collaborative_writing.py

from generic import *


###########################
##   Datastore Objects   ##
###########################

# Should have a Project as parent
class CollaborativeWritings(db.Model):
    title = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = True)

######################
##   Web Handlers   ##
######################

class NewWritingPage(GenericPage):
    def get(self, project_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        project = self.get_item_from_key_str(project_key)
        if project:
            params = {}
            params["error"] = ''
            params["project_key"] = project_key
            params["submit_button_text"] = "Create new writing"
            if not project.user_is_author(user):
                params["error"] = "You are not an author for this project."
            self.render("writing_description.html", **params)
        else:
            logging.debug("Handler NewWritingPage tryed to fetch a non-existing project")
            self.error(404)

    def post(self, project_key):
        user = self.get_user()
        if not user:
            self.redirect("/login")
            return
        project = self.get_item_from_key_str(project_key)
        if not project:
            logging.debug("Handler NewWritingPage tryed to fetch a non-existing project")
            self.error(404)
            return
        params = {"project" : project, "project_key" : project_key, "error" : "", 
                  "submit_button_text" : "Create new writing"}
        params["title"] = self.request.get("title")
        params["description"] = self.request.get("description")
        have_error = False
        if not project.user_is_author(user):
            have_error = True
            params["error"] = "You are not an author for this project. "
        if not params["title"]:
            have_error = True
            params["error"] += "Please provide a title. "
        if not params["description"]:
            have_error = True
            params["error"] += "Please provide a brief description of the purpose of this new writing. "
        if have_error:
            self.render("writing_description.html", **params)
        else:
            new_writing = CollaborativeWritings(title = params["title"], description = params["description"],
                                               parent = project)
            logging.debug("DB WRITE: Handler NewWritingPage is creating a new CollaborativeWriting")
            new_writing.put()
            self.redirect("/projects/project/%s/cwriting/%s" % (project_key, new_writing.key()))

class WritingPage(GenericPage):
    def get(self, project_key, writing_key):
        self.write("<html><body>" + project_key + "<br/>" + writing_key + "</body></html>")
