import os

if __name__ == '__main__':
    root = "/users/apple"
    # username = "tototobage"
    # filename = "first.py"
    #
    # os.chdir(root)      # cd /users/apple
    # os.mkdir(username)  # mkdir tototobage
    # os.chdir(username)
    #
    # with open(filename, "wb") as fb:
    #     fb.write(b"hello world")

    # print(os.path.exists(root))

    path = os.path.join("/users/apple", "to2bage")
    print(os.path.exists(path))

    os.mkdir(path)
    print(os.path.exists(path))

    pass