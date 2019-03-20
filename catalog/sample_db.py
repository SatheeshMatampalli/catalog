from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from projector_DB import *
engine = create_engine('sqlite:///projector_databse.db', connect_args={
                       'check_same_thread': False}, echo=True)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

# Delete Brand
session.query(Brand_Data).delete()
# Delete ModelName
session.query(Model_Data).delete()
# Delete Users
session.query(User_Data).delete()

# Create sample users
User11 = User_Data(name="Sateesh",
                   email="m.satheesh566@gmail.com",
                   picture='https://lh5.googleusercontent.com/-6tCX9WOltBs'
                         '/AAAAAAAAAAI/AAAAAAAADJc/T4yOqe2XIjc/photo.jpg')
session.add(User11)
session.commit()
User22 = User_Data(name="Satheesh matampalli", email="m.satheesh566@gmail.com",
                   picture='https://lh4.googleusercontent.com/-EW6n0vdHiOk'
                   '/AAAAAAAAAAI/AAAAAAAAAE4/kHbfWo9laMw/photo.jpg')
session.add(User22)
session.commit()

# Create sample Brands
Brand11 = Brand_Data(name="Hitachi", user_id=1)
session.add(Brand11)
session.commit()

Brand22 = Brand_Data(name="BenQ", user_id=1)
session.add(Brand22)
session.commit

try:
    Model11 = Model_Data(id=1001, brand_id=1,
                         user_id=1, modelno="789",
                         colors="White", cost="1500",
                         description="Quality is Fine")
    session.add(Model11)
    session.commit()
except Exception as ex:
    print(ex)

try:
    Model22 = Model_Data(id=1002,
                         brand_id=2,
                         user_id=2,
                         modelno="026",
                         colors="Black",
                         cost="300",
                         description="Good Quality")
    session.add(Model22)
    session.commit()
except Exception as ex:
    print(ex)
print("Sample Data Base Content.............!")
