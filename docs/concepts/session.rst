.. _session:

Session
=======

.. attention::

    The ``Session`` object is completely optional in a config.

The ``Session`` object in a config represents parameters for :class:`boto3.session.Session`.

``Session`` can accept the following parameters in your config file:

.. code-block:: yaml

    Session:
      region_name: str
      profile_name: str
      aws_account_id: str
      aws_access_key_id: str
      aws_secret_access_key: str
      aws_session_token: str