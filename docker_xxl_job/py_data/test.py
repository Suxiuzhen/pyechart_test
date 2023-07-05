import time
def test():
    with open('./test.txt', 'w+') as f:
        f.write(str(time.time()))

if __name__ == '__main__':
    test()
