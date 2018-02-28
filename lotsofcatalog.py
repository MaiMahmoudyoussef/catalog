from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Item, User

engine = create_engine('sqlite:///catalogitems.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()
category1 = Category(user_id=1, name="Soccer")
session.add(category1)
session.commit()

category2 = Category(user_id=2, name="Basketball")
session.add(category2)
session.commit()

category3 = Category(user_id=3, name="Baseball")
session.add(category3)
session.commit()

category4 = Category(user_id=4, name="Frisbee")
session.add(category4)
session.commit()

category5 = Category(user_id=5, name="Snowboarding")
session.add(category5)
session.commit()


item1 = Item(user_id=1, name="Goggles", description="Best fro any terrian and condition",
                     category=category5)

session.add(item1)
session.commit()
