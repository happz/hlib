import gzip
import StringIO
import struct

def compress(data, level = 6):
  stream = StringIO.StringIO()
  gzipper = gzip.GzipFile(mode = 'wb', compresslevel = level, fileobj = stream)
  gzipper.write(data)
  gzipper.close()

  return stream.getvalue()
