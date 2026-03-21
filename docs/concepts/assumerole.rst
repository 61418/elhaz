.. _assumerole:

AssumeRole
==========

.. attention::

    The only required parameter for the ``AssumeRole`` object is ``RoleArn``.
    All other parameters are completely optional.

The ``AssumeRole`` object in a config represents parameters for :meth:`STS.Client.assume_role`.

``AssumeRole`` can accept the following parameters in your config file:

.. code-block:: yaml

    AssumeRole:
      RoleArn: str
      RoleSessionName: str
      ExternalId: str
      SerialNumber: str
      TokenCode: str
      SourceIdentity: str
      Policy: str
      PolicyArns:
        - str
      Tags:
        - Key: str
          Value: str
      TransitiveTagKeys:
        - str
      ProvidedContexts:
        - ProviderArn: str
          ContextAssertion: str