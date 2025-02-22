# AISecretAgent
Evolving AI agent workflows

Idea

Explore if we can evolve AI agent workflows through a genetic approach.

Assuming we are trying to solve a specific type of problems. We also assume we have a training set of problems with answers.
The idea is to generate a set of agentic workflows to try to solve this type of problems and to use genetic algorithms to evolve the workflows towards increase ability to solve the problems in the training set.

An AI worker is:
- a function that takes an input and produces an output
- uses an AI system (usually an LLM) to produce the output
- has a well defined role and interface

An AI workflow is a function:
- that given an input (prompt/problem/question)
- returns an output (solution/response)
- achieves this by chaining multiple AI workers

Problem->AI workflow->Solution

Ex. simple workflow:
Problem->Worker1->Worker2->Solution