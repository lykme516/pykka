#! /usr/bin/env python

import sys
import time
#import networkx as nx
#import pandas as pd
#import numpy as np
import random
#import matplotlib.pyplot as plt

import pykka

class BasicActor(pykka.ThreadingActor):
    """ DOC STRING """
    def __init__(self, greeting='Hi there!'):
        # You can override __init__ to pass args, but super().__init__() must be called
        super().__init__()
        self.greeting = greeting
        self.data = list()
        self.response = str()

    def generate_data(self, sample_size):
        """ For this simple example, we are limiting data creation per worker to 100 units.
        When scaling the application, the supervisor should consider spawning more child actors."""
        if sample_size >= 100:
            raise IOError("Basic Actors are limited to sample size of 100. \
            Supervisor needs to reallocate work")
        self.data = [random.randint(1, 101) for i in range(sample_size)]
        print("DEBUG: {} completed data with \n {}".format(self.actor_urn, self.data))

    def emulate_fail(self):
        raise Exception("Mock Exception for testing purposes")

    def clear(self):
        self.data.clear()

class Supervisor(BasicActor):
    """ A basic example of how an actor can take on the super visor role. """
    def __init__(self, num_child=5, num_error=1):
        if (num_child > 5 or not isinstance(num_child, int)):
            raise IOError("Supervisor is limited to 5 children and integer args.")
        super().__init__()
        self.num_child = num_child
        self.list_actors = list()

    def _clean_up(self):
        print("INFO: Cleaning up all actors.")
        for actor in self.list_actors:
            actor.clear()
            actor.stop()

    def create_workers(self):
        for i in range(self.num_child):
            try:
                self.list_actors.append(BasicActor.start().proxy())
            except IOError:
                #Do not stop execution on a actor exception. Start as many jobs as possible.
                print("WARNING: child actor {} was wrongfully partitioned work".
                      format(self.num_child))
            except:
                print("ERROR: child actor {} failed to spawn due to {}.".
                      format(self.num_child, sys.exc_info()[0]))
        print("DEBUG: {} child actors were spawned.".format(len(self.list_actors)))
        print("DEBUG: {}".format(self.list_actors))

    def start_work_day(self):
        for actor_proxy in self.list_actors:
            print("INFO:------ {} ---------".format(actor_proxy.actor_ref.actor_urn))
            actor_proxy.generate_data(10)
        print(self.list_actors)

    def stop_work_day(self):
        self._clean_up()

if __name__ == '__main__':
    SUPER_A = None
    try:
        SUPER_A = Supervisor(num_child=1, num_error=1)
        SUPER_A.create_workers()
        SUPER_A.start_work_day()
        while 0:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    except Exception:
        print("ERROR: {}".format(sys.exc_info()[0]))

    if isinstance(SUPER_A, Supervisor):
        SUPER_A.stop_work_day()
