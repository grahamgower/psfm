import base64

files = ["x.gif", "x_red.gif"]
for f in files:
    with open(f, 'rb') as fd:
        encoded = base64.encodestring(fd.read())
        data = encoded.decode('latin1')
        print("\"\"\"\n{}\"\"\",".format(data))
