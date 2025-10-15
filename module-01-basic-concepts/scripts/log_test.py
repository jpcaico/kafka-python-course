from log import SimpleLog
from wrappers.utils import sumi


log = SimpleLog()

#print(f"Initial log size: {len(log.records)}")


log.append("First value")
log.append(123)
log.append({"key":"value"}) #2

# print(f"Log size: {len(log.records)}")

# print(f"Latest offset: {log.latest_offset()}")


print(log.read(1))

log.records[1] = 456

print(log.read(1))


# print(log.read_from(1))

# print(log)

print(sumi(2,3))