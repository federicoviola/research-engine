# notebooks.py
# All related to Notebooks and Notes inside a project.

from generic import *
import projects


###########################
##   Datastore Objects   ##
###########################

# Notebooks have a Project as parent.
class Notebooks(ndb.Model):
    owner = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    name = ndb.StringProperty(required = True)
    description = ndb.TextProperty(required = True)
    started = ndb.DateTimeProperty(auto_now_add = True)
    last_updated = ndb.DateTimeProperty(auto_now = True)

# Each note should be a child of a Notebook.
class NotebookNotes(ndb.Model):
    title = ndb.StringProperty(required = True)
    content = ndb.TextProperty(required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)

    def notification_html_and_txt(self, author, project, notebook):
        kw = {"author" : author, "project" : project, "notebook" : notebook, "note" : self,
              "author_absolute_link" : DOMAIN_PREFIX + "/" + author.username}
        kw["project_absolute_link"] = DOMAIN_PREFIX + "/" + str(project.key.integer_id())
        kw["notebook_absolute_link"] = kw["project_absolute_link"] + "/notebooks/" + str(notebook.key.integer_id())
        kw["note_absolute_link"] = kw["notebook_absolute_link"] + "/" + str(self.key.integer_id())
        return (render_str("emails/note.html", **kw), render_str("emails/note.txt", **kw))

# Each comment should be a child of a NotebookNote
class NoteComments(ndb.Model):
    author = ndb.KeyProperty(kind = RegisteredUsers, required = True)
    date = ndb.DateTimeProperty(auto_now_add = True)
    comment = ndb.TextProperty(required = True)

    def notification_html_and_txt(self, author, project, notebook, note):
        kw = {"author" : author, "project" : project, "notebook" : notebook, "note" : note, "comment" : self,
              "author_absolute_link" : DOMAIN_PREFIX + "/" + author.username}
        kw["project_absolute_link"] = DOMAIN_PREFIX + "/" + str(project.key.integer_id())
        kw["notebook_absolute_link"] = kw["project_absolute_link"] + "/notebooks/" + str(notebook.key.integer_id())
        kw["note_absolute_link"] = kw["notebook_absolute_link"] + "/" + str(self.key.integer_id())
        return (render_str("emails/note_comment.html", **kw), render_str("emails/note_comment.txt", **kw))


######################
##   Web Handlers   ##
######################

class NotebookPage(projects.ProjectPage):
    def get_notebooks_list(self, project, log_message = ''):
        notebooks = []
        for n in Notebooks.query(ancestor = project.key).order(-Notebooks.last_updated).iter():
            self.log_read(Notebooks, log_message)
            notebooks.append(n)
        return notebooks

    def get_notebook(self, project, nbid, log_message = ''):
        self.log_read(Notebooks, log_message)
        return Notebooks.get_by_id(int(nbid), parent = project.key)

    def get_notes_list(self, notebook, log_message = ''):
        notes = []
        for n in NotebookNotes.query(ancestor = notebook.key).order(-NotebookNotes.date).iter():
            self.log_read(NotebookNotes, log_message)
            notes.append(n)
        return notes

    def get_note(self, notebook, note_id, log_message = ''):
        self.log_read(NotebookNotes, log_message)
        return NotebookNotes.get_by_id(int(note_id), parent = notebook.key)

    def get_comments_list(self, note, log_message = ''):
        comments = []
        for c in NoteComments.query(ancestor = note.key).order(NoteComments.date).iter():
            self.log_read(NoteComments, log_message)
            comments.append(c)
        return comments


class NotebooksListPage(NotebookPage):
    def get(self, projectid):
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebooks = self.get_notebooks_list(project)
        self.render("notebooks_list.html", project = project, 
                    notebooks = notebooks, n_len = len(notebooks))


class NewNotebookPage(NotebookPage):
    def get(self, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/notebooks/new'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project: 
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        visitor_p = False if project.user_is_author(user) else True
        kw = {"title" : "New notebook",
              "name_placeholder" : "Title of the new notebook",
              "content_placeholder" : "Description of the new notebook",
              "submit_button_text" : "Create notebook",
              "cancel_url" : "/%s/notebooks" % project.key.integer_id(),
              "title_bar_extra" : '/ <a href="/%s/notebooks">Notebooks</a>' % project.key.integer_id(),
              "more_head" : "<style>.notebooks-tab {background: white;}</style>",
              "disabled_p" : True if visitor_p else False,
              "pre_form_message" : '<span style="color:red;">You are not an author in this project.</span>' if visitor_p else ""}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/notebooks/new'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        have_error = False
        error_message = ''
        visitor_p = False if project.user_is_author(user) else True
        if visitor_p:
            have_error = True
            error_message = "You are not an author in this project. "
        n_name = self.request.get("name")
        n_description = self.request.get("content")
        if not n_name:
            have_error = True
            error_message = "You must provide a name for your new notebook. "
        if not n_description:
            have_error = True
            error_message += "Please provide a description of this notebook. "
        if have_error:
            kw = {"title" : "New notebook",
                  "name_placeholder" : "Title of the new notebook",
                  "content_placeholder" : "Description of the new notebook",
                  "submit_button_text" : "Create notebook",
                  "cancel_url" : "/%s/notebooks" % project.key.integer_id(),
                  "title_bar_extra" : '/ <a href="/%s/notebooks">Notebooks</a>' % project.key.integer_id(),
                  "more_head" : "<style>.notebooks-tab {background: white;}</style>",
                  "name_value" : n_name,
                  "content_value" : n_description,
                  "error_message" : error_message,
                  "disabled_p" : True if visitor_p else False,
                  "pre_form_message" : '<span style="color:red;">You are not a member of this project.</span>' if visitor_p else ""}
            self.render("project_form_2.html", project = project, **kw)
        else:
            new_notebook = Notebooks(owner = user.key, 
                                     name = n_name, 
                                     description = n_description, 
                                     parent  = project.key)
            self.log_and_put(new_notebook)
            self.log_and_put(project, "Updating last_updated property. ")
            self.redirect("/%s/notebooks/%s" % (project.key.integer_id(), new_notebook.key.id()))


class NotebookMainPage(NotebookPage):
    def get(self, projectid, nbid):
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        notes = self.get_notes_list(notebook)
        self.render("notebook_main.html", project = project, notebook = notebook, notes = notes)


class NewNotePage(NotebookPage):
    def get(self, projectid, nbid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/notebooks/' + nbid + "/new_note"
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        visitor_p = False if notebook.owner.get().key == user.key else True
        parent_url = "/%s/notebooks" % project.key.integer_id()
        kw = {"title" : "New note",
              "name_placeholder" : "Title of the new note",
              "content_placeholder" : "Content of the note",
              "submit_button_text" : "Create note",
              "cancel_url" : "%s/%s" % (parent_url, nbid),
              "markdown_p" : True,
              "more_head" : "<style>.notebooks-tab {background: white;}</style>",
              "title_bar_extra" : '/ <a href="%s">Notebooks</a> / <a href="%s">%s</a>' % (parent_url, parent_url + '/' + str(notebook.key.integer_id()), notebook.name),
              "disabled_p" : True if visitor_p else False,
              "pre_form_message" : '<span style="color:red;">You are not the owner of this notebook.</span>' if visitor_p else ""}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid, nbid):
        user = self.get_login_user()
        if not user:
            goback = '/' + username + '/' + projectid + '/notebooks/' + nbname + '/new_note'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        have_error = False
        error_message = ''
        visitor_p = False if notebook.owner.get().key == user.key else True
        n_title = self.request.get("name")
        n_content = self.request.get("content")
        if visitor_p:
            have_error = True
            error_message = "You are not the owner of this notebook. "
        if not n_title:
            have_error = True
            error_message = "Please provide a title for this note. "
        if not n_content:
            have_error = True
            error_message += "You need to write some content before saving this note. "
        if have_error:
            parent_url = "/%s/notebooks" % (project.key.integer_id())
            kw = {"title" : "New note",
                  "name_placeholder" : "Title of the new note",
                  "content_placeholder" : "Content of the note",
                  "submit_button_text" : "Create note",
                  "cancel_url" : "%s/%s" % (parent_url ,notebook.key.integer_id()),
                  "markdown_p" : True,
                  "more_head" : "<style>.notebooks-tab {background: white;}</style>",
                  "title_bar_extra" : '/ <a href="%s">Notebooks</a> / <a href="%s">%s</a>' % (parent_url, parent_url + '/' + str(notebook.key.integer_id()), notebook.name),
                  "name_value": n_title, "content_value": n_content, "error_message" : error_message,
                  "disabled_p" : True if visitor_p else False,
                  "pre_form_message" : '<span style="color:red;">You are not the owner of this notebook.</span>' if visitor_p else ""}
            self.render("project_form_2.html", project = project, **kw)
        else:
            new_note = NotebookNotes(title = n_title, content = n_content, parent = notebook.key)
            self.log_and_put(new_note)
            html, txt = new_note.notification_html_and_txt(user, project, notebook)
            self.add_notifications(category = new_note.__class__.__name__,
                                   author = user,
                                   users_to_notify = project.nb_notifications_list,
                                   html = html, txt = txt)
            self.log_and_put(notebook, "Updating last_updated property. ")
            self.log_and_put(project,  "Updating last_updated property. ")
            self.redirect("/%s/notebooks/%s/%s" % (projectid, nbid, new_note.key.integer_id()))


class NotePage(NotebookPage):
    def get(self, projectid, nbid, note_id):
        user = self.get_login_user()
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        note = self.get_note(notebook, note_id)
        if not note:
            self.error(404)
            self.render("404.html", info = 'Note with key <em>%s</em> not found' % note_id)
            return
        comments = self.get_comments_list(note)
        visitor_p = True if not (user and project.user_is_author(user)) else False
        error_message = ''
        if visitor_p and not user:
            error_message = "You must log in first to make a comment."
        elif visitor_p and not project.user_is_author(user):
            error_message = "You are not an author in this project."
        self.render("notebook_note.html", project = project, visitor_p = visitor_p, error_message = error_message,
                    notebook = notebook, note = note, comments = comments)

    def post(self, projectid, nbid, note_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/notebooks/' + nbid + '/' + note_id
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        note = self.get_note(notebook, note_id)
        if not note:
            self.error(404)
            self.render("404.html", info = 'Note with key <em>%s</em> not found' % note_id)
            return
        have_error = False
        error_message = ''
        visitor_p = True if not project.user_is_author(user) else False
        if visitor_p:
            have_error = True
            error_message = "You are not an author in this project."
        comment = self.request.get("comment")
        if not comment:
            have_error = True
            error_message = "You can't submit an empty comment. "
        if not have_error:
            new_comment = NoteComments(author = user.key, comment = comment, parent = note.key)
            self.log_and_put(new_comment)
            html, txt = new_comment.notification_html_and_txt(user, project, notebook, note)
            self.add_notifications(category = new_comment.__class__.__name__,
                                   author = user,
                                   users_to_notify = project.nb_notifications_list,
                                   html = html, txt = txt)
            self.log_and_put(notebook, "Updating its last_updated property. ")
            self.log_and_put(project, "Updating its last_updated property. ")
            comment = ''
        comments = self.get_comments_list(note)
        self.render("notebook_note.html", project = project, visitor_p = visitor_p,
                    notebook = notebook, note = note, comments = comments, 
                    comment = comment, error_message = error_message)


class EditNotebookPage(NotebookPage):
    def get(self, projectid, nbid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/notebooks/' + nbid + '/edit'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        visitor_p = False if notebook.owner.get().key == user.key else True
        nbs_url = "/%s/notebooks" % projectid
        nb_url = nbs_url + "/" + nbid
        kw = {"title" : "Edit notebook: %s" % notebook.name,
              "name_placeholder" : "Title of the notebook",
              "content_placeholder" : "Description of the notebook",
              "submit_button_text" : "Save Changes",
              "cancel_url" : "/%s/notebooks/%s" % (projectid, nbid),
              "more_head" : "<style>.notebooks-tab {background: white;}</style>",
              "title_bar_extra" : '/ <a href="%s">Notebooks</a> / <a href="%s">%s</a>' 
              % (nbs_url, nb_url, notebook.name),
              "name_value" : notebook.name,
              "content_value" : notebook.description,
              "markdown_p" : True,
              "disabled_p" : True if visitor_p else False,
              "pre_form_message" : '<span style="color:red;">You are not the owner of this notebook.</span>' if visitor_p else ""}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid, nbid):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/notebooks/' + nbname + '/edit'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        have_error = False
        error_message = ''
        visitor_p = False if notebook.owner.get().key == user.key else True
        if visitor_p:
            have_error = True
            error_message = "You are not the owner of this notebook. "
        n_name = self.request.get("name")
        n_description = self.request.get("content")
        if not n_name:
            have_error = True
            error_message = "You must provide a name for the notebook. "
        if (not n_description) or (len(n_description.strip()) == 0):
            have_error = True
            error_message += "Please provide a description of this notebook. "
        if have_error:
            nbs_url = "/%s/notebooks" % (projectid)
            nb_url = nbs_url + "/" + nbid
            kw = {"title" : "Edit notebook: %s" % notebook.name,
                  "name_placeholder" : "Title of the notebook",
                  "content_placeholder" : "Description of the notebook",
                  "submit_button_text" : "Save Changes",
                  "cancel_url" : "/%s/notebooks/%s" % (projectid, nbid),
                  "more_head" : "<style>.notebooks-tab {background: white;}</style>",
                  "title_bar_extra" : '/ <a href="%s">Notebooks</a> / <a href="%s">%s</a>' 
                  % (nbs_url, nb_url, notebook.name),
                  "name_value" : n_name,
                  "content_value" : n_description,
                  "error_message" : error_message,
                  "markdown_p" : True,
                  "disabled_p" : True if visitor_p else False,
                  "pre_form_message" : '<span style="color:red;">You are not the owner of this notebook.</span>' if visitor_p else ""}
            self.render("project_form_2.html", project = project, **kw)
        else:
            notebook.name = n_name
            notebook.description = n_description
            self.log_and_put(notebook)
            self.redirect("/%s/notebooks/%s" % (projectid, nbid))


class EditNotePage(NotebookPage):
    def get(self, projectid, nbid, note_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + "/notebooks/" + nbid + '/' + note_id + '/edit'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        note = self.get_note(notebook, note_id)
        if not note:
            self.error(404)
            self.render("404.html", info = 'Note with key <em>%s</em> not found' % note_id)
            return
        visitor_p = False if notebook.owner.get().key == user.key else True
        nbs_url = "/%s/notebooks" % projectid
        nb_url = nbs_url + "/" + nbid
        note_url = nb_url + "/" + note_id
        kw = {"title" : "Edit note",
              "name_placeholder" : "Title of the note",
              "content_placeholder" : "Content of the note",
              "submit_button_text" : "Save changes",
              "markdown_p" : True,
              "cancel_url" : note_url,
              "more_head" : "<style>.notebooks-tab {background: white;}</style>",
              "title_bar_extra" : '/ <a href="%s">Notebooks</a> / <a href="%s">%s</a> / <a href="%s">%s</a>' 
              % (nbs_url, nb_url, notebook.name, note_url, note.title),
              "name_value" : note.title, "content_value" : note.content,
              "disabled_p" : True if visitor_p else False,
              "pre_form_message" : '<span style="color:red;">You are not the owner of this notebook.</span>' if visitor_p else ""}
        self.render("project_form_2.html", project = project, **kw)

    def post(self, projectid, nbid, note_id):
        user = self.get_login_user()
        if not user:
            goback = '/' + projectid + '/notebooks/' + nbid + '/' + note_id + '/edit'
            self.redirect("/login?goback=%s" % goback)
            return
        project = self.get_project(projectid)
        if not project:
            self.error(404)
            self.render("404.html", info = 'Project with key <em>%s</em> not found' % projectid)
            return
        notebook = self.get_notebook(project, nbid)
        if not notebook:
            self.error(404)
            self.render("404.html", info = 'Notebook with key <em>%s</em> not found' % nbid)
            return
        note = self.get_note(notebook, note_id)
        if not note:
            self.error(404)
            self.render("404.html", info = 'Note with key <em>%s</em> not found' % note_id)
            return
        have_error = False
        error_message = ''
        visitor_p = False if notebook.owner.get().key == user.key else True
        if visitor_p:
            have_error = True
            error_message = "You are not the owner of this notebook. "
        n_title = self.request.get("name")
        n_content = self.request.get("content")
        if not n_title:
            have_error = True
            error_message = "Please provide a title for this note. "
        if not n_content:
            have_error = True
            error_message += "You need to write some content before saving this note. "
        if have_error:
            kw = {"title" : "New note",
                  "name_placeholder" : "Title of the new note",
                  "content_placeholder" : "Content of the note",
                  "submit_button_text" : "Create note",
                  "cancel_url" : "/%s/notebooks/%s" % (projectid, nbid),
                  "more_head" : "<style>.notebooks-tab {background: white;}</style>",
                  "name_value": n_title, "content_value": n_content, "error_message" : error_message,
                  "disabled_p" : True if visitor_p else False,
                  "pre_form_message" : '<span style="color:red;">You are not the owner of this notebook.</span>' if visitor_p else ""}
            self.render("project_form_2.html", project = project, **kw)
        else:
            if (note.title != n_title) or (note.content != n_content):
                note.title = n_title
                note.content = n_content
                self.log_and_put(note)
            self.redirect("/%s/notebooks/%s/%s" % (projectid, nbid, note_id))

