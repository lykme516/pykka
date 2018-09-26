'''
Simple example of how to use a router and manage routees from within an actor.

https://doc.akka.io/docs/akka/current/routing.html?language=scala

Essentially, create a Router actor. Someone who manages the routees and
loads routing logic and other settings from configuration.

Pool vs. Group

Pool, the router creates routees as child actors and removes them from the router if they terminate

Group, the routee actors are created externally to the router and the router sends messages to the
specified path using actor selection, without watching for termination.


ActorRef router1 =
  getContext().actorOf(FromConfig.getInstance().props(Props.create(Worker.class)), 
    "router1");

ActorRef router2 =
  getContext().actorOf(new RoundRobinPool(5).props(Props.create(Worker.class)), 
    "router2");

Actor ref is 
'''