from flask_security import SQLAlchemyUserDatastore         #clssed have predefinied methods which r necessary to retrieve authenticatn token
from controllers.database import db
from controllers.models import User,Roles

user_datastore=SQLAlchemyUserDatastore(db,User,Roles)