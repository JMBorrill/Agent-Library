"""agentlib: tooling for the professional agent and skills library.

The package provides:

* ``agentlib.validate`` - structural validators for skills, agents, commands,
  workflows, catalogs and the generated registry.
* ``agentlib.frameworks`` - deterministic tools derived from the bundled
  framework sources (NASA, NIST, OWASP, HM Treasury). Each module may expose
  ``register(subparsers)`` to add a CLI sub-command; modules are discovered
  automatically.
* ``agentlib.evals`` - the evaluation harness for skills.

Nothing in this package certifies engineering, security or regulatory
compliance. Tools support professional judgement; they do not replace it.
"""

__version__ = "0.1.0"
