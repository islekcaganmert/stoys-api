from stoys import STOYS

session = STOYS(input('Username: '), input('Password: '))
r = session.resources()
print(len(r))
print(r[0])
