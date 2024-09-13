from consume import c

result = add.delay(4, 4)
print('Waiting for result...')
print('Result:', result.get())
