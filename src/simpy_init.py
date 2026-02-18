
import simpy

def hola(env):
    while True:
        print(f"{env.now}: Hola mundo desde el proceso 'hola'")
        yield env.timeout(1)  #esperar 1 unidad de tiempo

env = simpy.Environment()
env.process(hola(env))    #arrancar el proceso
env.run(until=5)         #ejecutar la simulación hasta t = 5
