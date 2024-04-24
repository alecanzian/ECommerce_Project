import sqlalchemy as sq
from sqlalchemy import MetaData, Table, Column, ForeignKey

# SQLite supporta database transienti in RAM (echo attiva il logging)
engine = sq.create_engine('sqlite:///C:/Users/utente/Desktop/UNIVE/vsc/BD/database.db',echo = True)

#possiamo cheidere all'engine di effettuare una connessione al database (ricordatevi di chiuderla)
#possiamo usare la connessione pr inviare query al database e ricevere il risultato
#with engine.connect() as conn:
  #conn.execute(sq.text("CREATE TABLE some_table (x int, y int)"))
  #conn.commit()

  #conn.execute(sq.text("INSERT INTO some_table (x, y) VALUES (1,2)"))
  #conn.execute(sq.text("INSERT INTO some_table (x, y) VALUES (3,4)"))
  #conn.execute(sq.text("INSERT INTO some_table (x, y) VALUES (5,6)"))
  #result = conn.execute(sq.text("SELECT x,y FROM some_table"))
  #for row in result:
  #  print(f"x: {row.x}  y: {row.y}")
  #for a,b in result:
  #  print(f"x: {a}  y: {b}")
#conn.commit()  #ATTENZIONE: di default SQLAlchemy non usa l'autocommit
  
metadata = MetaData()
#users = Table('users', metadata, Column('id', sq.Integer, primary_key=True), #primary key
#                                Column('name', sq.String),
#                                Column('fullname', sq.String))
#
#addresses = Table('addresses', metadata, Column('id', sq.Integer, primary_key=True),
#                                        Column('user_id', None, ForeignKey('users.id'), nullable=False), #non serve specificare il tipo se foreign key
#                                        Column('email_address', sq.String, nullable=False)) #NOT NULL
#
#metadata.create_all(engine)  # creazione dello schema nel DB
users = Table('users', metadata, autoload_with = engine)
addresses = Table('addresses', metadata, autoload_with = engine)
#ins = sq.insert(users).values(name='John', fullname=" John Doe")
ins = sq.insert(users)
#print([c.name for c in users.columns])
s = sq.select(users)
with engine.begin() as conn:
    #conn.execute(ins, {'name': 'wendy', 'fullname': 'Wendy Williams'})
    #conn.execute(ins, {'name': 'sally', 'fullname': 'Sally Roberts'})
    #conn.execute(ins, {'name': 'wendy', 'fullname': 'Wendy Roberts'})
    #conn.execute(addresses.insert(), [{'user_id': 1, 'email_address' : 'jack@yahoo.com'},
    #                                    {'user_id': 1, 'email_address' : 'jack@msn.com'},
    #                                    {'user_id': 2, 'email_address' : 'www@www.org'},
    #                                    {'user_id': 2, 'email_address' : 'wendy@aol.com'}])

    result= conn.execute(s)
    for row in result: #rimanenti
      print (row)
    s = sq.select(addresses)
    for row  in conn.execute(s):
       print(row)
    for row in conn.execute(sq.select(users, addresses).where(users.c.id == addresses.c.user_id)):
       print(row)
