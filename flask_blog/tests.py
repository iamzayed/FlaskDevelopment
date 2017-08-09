# Set the path
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import sqlalchemy
from flask.ext.sqlalchemy import SQLAlchemy

from flask_blog import app, db

# need to add all models for db.create_all to work
from author.models import *
from blog.models import *

class UserTest(unittest.TestCase):
    def setUp(self):
        self.db_uri = 'mysql+pymysql://%s:%s@%s/' % (app.config['DB_USERNAME'], app.config['DB_PASSWORD'], app.config['DB_HOST'])
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['BLOG_DATABASE_NAME'] = 'test_blog'
        app.config['SQLALCHEMY_DATABASE_URI'] = self.db_uri + app.config['BLOG_DATABASE_NAME']
        engine = sqlalchemy.create_engine(self.db_uri)
        conn = engine.connect()
        conn.execute("commit")
        conn.execute("create database "  + app.config['BLOG_DATABASE_NAME'])
        db.create_all()
        conn.close()
        self.app = app.test_client()

    def tearDown(self):
        db.session.remove()
        engine = sqlalchemy.create_engine(self.db_uri)
        conn = engine.connect()
        conn.execute("commit")
        conn.execute("drop database "  + app.config['BLOG_DATABASE_NAME'])
        conn.close()

    def create_blog(self):
        return self.app.post('/setup', data=dict(
            name='My Test Blog',
            fullname='Tester Tester',
            email='tester@fromzero.io',
            username='tester',
            password='12345',
            confirm='12345'
            ),
        follow_redirects=True)

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def register_user(self, fullname, email, username, password, confirm):
        return self.app.post('/register', data=dict(
            fullname=fullname,
            email=email,
            username=username,
            password=password,
            confirm=confirm
            ),
        follow_redirects=True)

    def publish_post(self, title, body, category, new_category):
        return self.app.post('/post', data=dict(
            title=title,
            body=body,
            category=category,
            new_category=new_category,
            ),
        follow_redirects=True)
    
    def create_comment(self, post_slug):return self.app.post('/article/' + post_slug, data=dict(
        body = 'This is a comment,This is a comment,This is a comment,This is a comment'), 
        follow_redirects=True)

    def delete_comment(self, comment_id):
        return self.app.get('/delete-comment/' + str(comment_id), follow_redirects=True)
      
# Notice that our test functions begin with the word test;
# this allows unittest to automatically identify the method as a test to run.
    
################################################################################
    #Asserts proper blog creation
    def test_create_blog(self):
        rv = self.create_blog()
        assert 'Blog created' in str(rv.data)
    
    #Asserts proper login and log out
    def test_login_logout(self):
        self.create_blog()
        rv = self.login('tester', '12345')
        assert 'User tester logged in' in str(rv.data)
        rv = self.logout()
        assert 'User logged out' in str(rv.data)
        rv = self.login('john', 'test')
        assert 'Author not found' in str(rv.data)
        rv = self.login('tester', 'wrong')
        assert 'Incorrect password' in str(rv.data)
    
    #Asserts proper registration
    def test_registration(self):
        rv = self.register_user( 'Tester2 Tester','tester2@mail.com','tester2','12345','12345')
        assert 'Author registered!' in str(rv.data)
      
    #Assert the admin functionality  
    def test_admin(self):
        self.create_blog()
        self.login('tester', '12345')
        rv = self.app.get('/admin', follow_redirects=True)
        assert 'Welcome, tester' in str(rv.data)
        rv = self.logout()
        rv = self.register_user('John Doe', 'john@example.com', 'john', 'test', 'test')
        assert 'Author registered!' in str(rv.data)
        rv = self.login('john', 'test')
        assert 'User john logged in' in str(rv.data)
        rv = self.app.get('/admin', follow_redirects=True)
        assert "403 Forbidden" in str(rv.data)
    
    #Asserts the create and delete comment function
    def test_create_delete_comment(self):
              
        self.create_blog()
        self.login('tester', '12345')
        self.publish_post('New New Title', 'bodyboydbody', None, 'Old Category')
       
        rv = self.create_comment('new-new-Title')
       
        assert 'Comment posted.' in str(rv.data)
        #Only one comment in database so the id is one
        rv = self.delete_comment(1)
        assert 'Comment deleted' in str(rv.data)
        
if __name__ == '__main__':
    unittest.main()