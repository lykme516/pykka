#! /usr/bin/env python

""" A basic example of implementing a supervisor in pykka. """
import time
import random
import enum

import pykka

class ChildStatus(enum.Enum):
    """ Standardize child state status for processing by Supervisor"""
    COMPLETED = 0
    NOT_STARTED = 1
    IN_PROGRESS = 2
    ERROR = 3

class BasicActor(pykka.ThreadingActor):
    """ DOC STRING """
    def __init__(self, greeting='Hi there!'):
        # You can override __init__ to pass args, but super().__init__() must be called
        super().__init__()
        self.greeting = greeting
        self.data = list()
        self.response = str()
        self.state = ChildStatus.NOT_STARTED

    def generate_data(self, sample_size):
        """ For this simple example, we are limiting data creation per worker to a max of 100 units. """
        if sample_size >= 100:
            raise IOError("Basic Actors are limited to sample size of 100. \
            Supervisor needs to reallocate work")
        for i in range(sample_size):
            if random.random() < .1:
                self.state = ChildStatus.ERROR
                print("ERROR: {} only completed {} data points.".format(self.actor_urn, i))
                return
            else:
                self.data.append(random.randint(1, 101))
        self.state = ChildStatus.COMPLETED
        print("DEBUG: {} completed data with \n {}".format(self.actor_urn, self.data))

class Supervisor(BasicActor):
    """ A basic example of how an actor can take on the super visor role. """
    def __init__(self, num_child=5):
        if (num_child > 5 or not isinstance(num_child, int)):
            raise IOError("{} is limited to 5 children and integer args.".
                          format(self.__class__.__name__))
        super().__init__()
        self.completed = False
        self.num_child = num_child
        self.list_actors = list()
        self.m_data = dict()

    def _clean_up(self):
        print("INFO: Cleaning up all actors.")
        for actor in self.list_actors:
            actor.stop()

    def create_workers(self):
        """ Create rolodex of workers that the Supervisor is in charge of """
        for i in range(self.num_child):
            try:
                tmp_actor = BasicActor.start().proxy()
                self.list_actors.append(tmp_actor)
                self.m_data[tmp_actor.actor_urn.get(timeout=0.1)] = list()
            except IOError:
                #Do not stop execution on a actor exception. Start as many jobs as possible.
                print("WARNING: child actor {} was wrongfully partitioned work".
                      format(self.num_child))
            except Exception as error:
                print("ERROR: child actor {} failed to spawn due to {}.".
                      format(self.num_child, error))

    def query_data(self):
        """Pull data from the child actors. """
        print("query_data {}".format(self.list_actors))
        if len(self.list_actors) == 0:
            self.completed = True
        else:
            for actor_proxy in self.list_actors:
                try:
                    if actor_proxy.state.get(timeout=0.1) is ChildStatus.COMPLETED:
                        # pull data and retire actor
                        self.m_data[actor_proxy.actor_urn.get()] = actor_proxy.data.get()
                        self.list_actors.remove(actor_proxy)
                        actor_proxy.stop()
                    elif actor_proxy.state.get(timeout=0.1) is ChildStatus.ERROR:
                        # kill child and start job again.
                        self.list_actors.remove(actor_proxy)
                        actor_proxy.stop()
                        new_actor_proxy = BasicActor.start().proxy()
                        self.list_actors.append(new_actor_proxy)
                        self.m_data[new_actor_proxy.actor_urn.get(timeout=0.1)] = list()
                        new_actor_proxy.generate_data(10)
                    else:
                        # attempt to pull data for reporting purposes
                        self.m_data[actor_proxy.actor_urn.get(timeout=0.1)] = (actor_proxy.data.get())
                except Exception as error:
                    print("Query data error: {}".format(error))

    def start_work_day(self):
        """ Explicitly alert all child actors to start their work. """
        for actor_proxy in self.list_actors:
            actor_proxy.generate_data(10)

    def stop_work_day(self):
        """ Explicitly close the work day. """
        self._clean_up()

if __name__ == '__main__':
    SUPER_A = None
    #import pdb; pdb.set_trace()
    try:
        SUPER_A = Supervisor(num_child=5)
        SUPER_A.create_workers()
        SUPER_A.start_work_day()
        while True:
            SUPER_A.query_data()
            if SUPER_A.completed == True:
                break
        print(SUPER_A.m_data)
        SUPER_A.stop_work_day()
    except Exception as error:
        print("ERROR: {}".format(error))
