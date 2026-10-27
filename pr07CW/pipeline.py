import subprocess as sp

p1 = sp.Popen(["ls"], stdout=sp.PIPE)
p2 = sp.Popen(["grep", "py"], stdin=p1.stdout, stdout = sp.PIPE, text=True)
p1.stdout.close()
out, _ = p2.communicate()
p1.wait()
print(out)
