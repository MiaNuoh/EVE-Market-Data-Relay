.. _overview:

A High-Level Overview
=====================

Project Motivation
------------------

The reason for this project's existence is that there are currently a large
number of barriers to entry for people wishing to start a project that relies
on EVE market data. A developer would probably need to:

* Either write their own uploader client, or re-purpose an existing uploader.
* Write a service/API to accept the data in whatever format(s) the uploader(s)
  they'd like to support use.
* Actually get players to point their uploader at said service/API (This is the
  hardest part!)
* Then, and only then, start writing the *fun* part of their application as
  the amount of data coming in slowly grows. By this point, they are probably
  a ways down the road to burnout.

If we can get some sort of a following organized around an instance of this
application, anyone wishing to work on a market-data driven project could
simply subscribe to our firehose of EVE market data.

Core Principles
---------------

* There should be no single point of failure. Every component of the
  architecture should be simple to make redundant using trusted volunteered
  machines.
* The application must be able to accept an extremely large number of incoming
  market orders without performance issues.
* It must be very easy to scale the system without restarts/reconfigs on the
  primary setup.
* The broadcasting of the market data needs to happen in a "fan out" manner.
  In this way, we can keep adding additional subscribers without running into
  scalability issues.

How it all fits together
------------------------

For any given submitted market order, here is the flow said order goes through::

    (Gateway) -> (Broker) -> (Processor) -> (Relay) -> (Applications, other Relays)

First, the order hits the **Gateway**, which is a very light WSGI application.
The only purpose of the gateway is to queue the order for submission to
a **Broker** daemon. Brokers are used to distribute raw order data out to any
of the many **Processor** daemons. The number of processor daemons can scale
up and down without any modifications or restarts of any of the components,
and it is super easy for external people to volunteer their machines by running
Processor daemons and getting permission to connect ot the Broker.
Order data gets passed between each component via ZeroMQ_, which is an extremely
scalable and performant transport/messaging layer.

Getting back to our example above, the **Processor** gets raw order data from
a **Broker**, looks at the raw data, parses it, performs some
really simple validation/verification, then passes it on to our top level
**Relay** via ZeroMQ_.

The **Relay** is a dumb repeater daemon. It takes the processed orders and just
spews them out to any subscribers. Subscribers can be other **Relay** daemons,
or actual user sites/applications. In the case of our eventual production
deployment, the top-level (tier-1) **Relay** will only speak to other relays.
The second level (tier-2) relays and lower are the ones that other
sites/applications can actually use. This keeps the load on our
top-level (tier-1) relay to a minimum, *meanwhile, allowing anyone to volunteer
to run tier-2 relays*.

.. _ZeroMQ: http://www.zeromq.org/

High Availability through shared burden
---------------------------------------

EMDR is architected in a way that allows every single component to be replicated
off-site. We can easily add additional daemons at each level of the stack in
order to increase throughput or availability.

EMDR contains no real security features of its own. Access will need to be
restricted at the OS/firewall level, and only trusted individuals should be
added to the stack.

Volunteering
------------

If you would like to volunteer computing resources to the EMDR network,
see :doc:`volunteering` for more details.