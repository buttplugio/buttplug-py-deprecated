Rationale
=========

I've been digitally pontificating about sex and technology since
sometime in 2004. During that time, I've noticed a recurring call for
a certain project: a unified protocol for controlling toys. One data
stream could define certain properties of a playback or communication
situation. For instance, imagine a movie that has abstract data
embedded in it about pressure, speed, friction, and other metrics
needed to replicate the physical situation. Toys that translate this
data already exist, but movies usually have to be encoded for a
specific toy. That toy may not work for all users, due to physical
differences, likes, dislikes, etc. What if we could make the data
abstract enough to work with any toy? Could we take that beyond movies
too, so that other interactive experiences such as games could harness
whatever hardware the user enjoyed most?

I've railed against every mention of this idea on the grounds of the
sheer amount of permutations it would have to encompass. Some toys
vibrate, some use friction, some use direction electrical stimulation
of nerves, some are one-offs beyond my imagination. How could we
possibly make a decent mapping of all of the data out of one data
stream?

Then one day, I realized something. The one question I never really
asked was "is it worth it to even try?". Every time the subject came
up, I just blew it off. But lately I've realized that the core system
of this idea would actually be fairly simple. A simple routing core,
that client applications could connect to, to either control toys, or
receive data from sensors. That's it. This is a workflow that comes up
constantly in other fields, so why not take a crack at doing it for
sex toys?

Thus, Buttplug began.

Design Considerations
=====================

Diverting into a quick software engineering discussion... 

Whenever I start a new software project, I try to define the
development portion as answers to 4 questions. These questions give me
a good outline to start on design and architecture choices for the
project. 

I tend to hop between projects a LOT. When I come back to a project,
these help me remember what I was doing and why I was doing it, so
that I can either understand context or fix things that I've learned
were a bad idea elsewhere.

What are we good at?
--------------------

The answer to this question should be an outline of skills we bring to
the table as software authors. We usually specialize in certain
languages or aspects of computation and architecture, which is
good to get out up front to set expectations.

In relation to Buttplug, this means:

**Accessing/Communicating with Computer Controlled Sex Toys**

Having reverse engineered more than a few of these in the past, I have
a good idea of what their protocols normally look like. This gives me
a good upfront view for designing a protocol to encompass all other
protocols.

**Writing Cross Platform Drivers**

Almost all of the drivers I've written in the past have been
completely cross platform. While this usually entails using a library
to do the heavy lifting (for low level usb, bluetooth, etc...), but
having knowledge of the platform eccentricities certainly helps in
design and testing.

**Connecting Things Together**

I've worked on sensor/actuator frameworks for robotics before. This
project is pretty much that, except less robots arms and self driving
cars and more fucktubes and pokey things. Ok and maybe some robot arms
too.


What are we not good at, or don't want to be good at?
-----------------------------------------------------

The fun part of writing open source software is that, usually, someone
else has done the hard and/or boring parts for you, and hopefully
better than you would anyways. This leaves you the ability to birth
your own new, boring software into the world. 
  
Answering this question with the aspects of the program we want
someone else doing is a great way to make a shopping list for
libraries.

In relation to Buttplug, this means:

**Low/Mid Level Hardware Protocols**

There's no reason to write our own USB/Firewire/Bluetooth/etc stacks.
Not only that, we don't even know what the future will hold in terms
of new connection mechanisms, or what languages they might be written
in.

We'll abstract away the hardware access using a process model. Each
piece of hardware will just have its own process that will talk to the
main routing process. That way, authors can just implement whatever
IPC we use and deal with the hardware specifics themselves. It does
mean that we'll get some library duplication across the system
sometimes, but eh, such is modern computing.

**Cross Language Bindings**

Trying to make a framework that forces everyone to write in the same
language seems silly when things like shared memory and real time
constraints aren't an issue. On top of that, having to figure out what
language has the most accessible FFI balanced against ease of
development just ends up wasting time. Most importantly, I've seen a
fuckton of sex software in my time, and let me tell you, a lot of
these people are in it for the love, not the code quality. Lots of
hastily cranked out VB and Delphi abound.

So we'll just let IPC be our cross language binding, and we'll pay for
it in the speed and data serialization. No big deal for the moment,
but it could come back to bite us at some point if we ever work with
hardware that requires a very high update rate.

**Cross Platform/Process Communication**

So what's the best solution for IPC? Pure networking usually works but
tends to be overly heavy (TCP) or overly light (UDP). Since ZeroMQ
already does IPC well enough for our needs and mostly solves the
problems of the network that we don't want to, and has all sorts of
langauge bindings already, we'll just go with that.

**Serialization**

Since we're going to push blocks of data back and forth over the wire,
we'll want to case that data up in a common way. There's myriad
solutions for this problem, including:

+ OSC
+ Protocol Buffers
+ msgpack
+ JSON
+ Rolling Our Own

Since we're in the "things we don't want to do" section of this
outline right now, the last one is out. OSC is usually married to UDP,
so we'd have to unwind parsing. Protocol Buffers and msgpack are both
quite popular, but msgpack comes with more of the data structures we
want. JSON may end up getting too large quickly, but at least means
we'll be able to read it in flight.

So it's between JSON and msgpack. Hopefully I'll remember to update
this document once I decide between the two.

What do we want to be good at when this is done?
------------------------------------------------

The abstract end goals of the software. Nebulous wording for what
finishing the project will get us. Hopefully non-technical, though
depending on the project that might be out of the question.

In relation to Buttplug, this means:

**Python**

I miss writing python, so that will be the main language for the
central router portion of the software. We can roll this into a binary
with all required libraries using cxFreeze.

Now also taking bets on how long it takes someone to completely
reimplement it in node.js once released.

**Simple Protocol Design**

I've been a part of some overly complex, overly engineered protocol
creation, as well as some stupid "throw it out there and deal with the
consequences" designs. I'd like to aim for the middle with this
protocol. Complex enough to be future proof, simple enough to be
understandable and easily implementable for future Delphi and VB sex
software developers.

**Removing the Problem of Hardware/Media Lock-in**

Once BP is done, you should hopefully be able to take media or
software created for one toy, and with a minimal amount of code, use
it with another toy taht it wasn't originally meant for. Beyond that,
we could also start working toward the aforementioned idea of abstract
data type that can be translated per toy.

**Supporting New Devices Quickly**

I write lots of proof of concepts for reverse engineered hardware. It
never really gets beyond that. Having a framework that I can plug
things into and have them "just work" would be quite motivating.

**Helping Others Make Interfaces**

Notice how back in the "Things we're good at" section, talking to
hardware was phrased as "accessing/communicating with"? That's because
I suck at the actual controls interfaces. You probably do to. Most
everyone does, because when it comes to sex, it's something that's
VERY specific to a single person. Now, not everyone can code. We
aren't expecting this to be an interface where anyone can quickly
implement their wildest fantasy without having seen a programming
language. But there are certainly developers out there who'd be happy
to help, and if all they had to worry about was the interface, not the
hardware, it'd make their lives far easier.

What do we not give a shit about?
---------------------------------

YAGNI early, YAGNI often. Lay out which parts of the system could
face scope creep. Any time it feels like something could be going
that direction, come back to this and smack yourself in the face
with it. Hard. Multiple times. Feel free to add to it as needed,
possibly written in blood drawn from smacking yourself in the face
with it.

In relation to Buttplug, this means:

**Security**

Yeah, I said it. I'm building a sex toy control framework and any
security feature that happens to land it in will be purely by
accident. The main reason for this is because security is HARD,
especially when we'll be trusting others to do things like write
plugins and clients. I don't really want that to be an issue up front,
so I'm not even going to act like it is. Don't go building a Sex Toy
as a Service framework with this piece of software. Use the design
ideas, but make sure you solve this hard problem, and it will be hard.

**IPC Communication Speed**

I've written libraries for controllers that have update rates in the
1khz range, and falling 10% below that will cause massive instability
in control loops. Those were not sex toys, or at least, were not
specifically intended to be as such. Sex toys could have that kind of
fidelity, but probably won't for a long while. Our most likely use
case will be one client talking to one piece of hardware. Anything we
support beyond that is great, and I'm sure we'll be able to support
10's if not 100's in a single router up front just due to the
frameworks we're planning on, but let's go for 1:1 first.
