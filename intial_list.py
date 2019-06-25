from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Game, User

# engine = create_engine('sqlite:///catalog.db')
engine = create_engine('postgresql://catalog:password@localhost/catalog')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
user = User(name='Mohamed Mansour', email='Mohamed.Mansour1196@gmail.com')

session.add(user)
session.commit()

c1 = Category(name="Action")

session.add(c1)
session.commit()

game1 = Game(name="Grand Theft Auto",
                  description="""GTA games have been around for a long time,
                                 with police pursuits, gunfights, gang wars,
                                 and huge open-world environments as mainstay
                                 The games have always had intense action,
                                 with the added bonus of much of it happening
                                 at high speeds in fast cars.Since police in
                                 the game willengage the player after just a
                                 few gunshots the ability to
                                 turn on the action"""
                  category=c1, user=user)
session.add(game1)
session.commit()


game2 = Game(name="Assassins Creed",
                  description="""explore historic locales all while fleeing
                                 or chasing using impressive free-running style
                                 movement. On top of that, the assassin-style
                                 stealth and endless and complex close-quarters
                                 battles keep the action high.
                                 With a broad arsenal of medieval
                                 weapons and more""",
                  category=c1, user=user)
session.add(game2)
session.commit()

game3 = Game(name="Red Dead Redemption",
                  description="""When Red Dead Redemption came out,
                                 Rockstar Games was already known for producing
                                 amazing open-world games with plenty of
                                 gun-slingingaction and essentially
                                 endless gameplay,thanks to the sandbox style
                                 of play.Plus a previous game in Red Dead""",
                  category=c1, user=user)

session.add(game3)
session.commit()

c2 = Category(name="Sports")
session.add(c2)
session.commit()
game4 = Game(name="FiFA",
                  description="""FIFA is a sports game that simulates association
                                 football,The game features 52 fully licensed
                                 stadiums from 12countries,including new
                                 stadiums,Commentary is
                                 provided by Martin Tyler"""
                  category=c2, user=user)
session.add(game4)
session.commit()
