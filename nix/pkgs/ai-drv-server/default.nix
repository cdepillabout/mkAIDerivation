{
  buildPythonPackage,
  flask,
  openai,
  requests,
  setuptools,
}:

buildPythonPackage rec {
  pname = "ai-drv-server";
  version = "0.0.1";

  # TODO: We should really filter out server/ai_drv_server/__pycache__/
  src = ../../../server;

  pyproject = true;

  build-system = [
    setuptools
  ];

  dependencies = [
    flask
    openai
    requests
  ];

  # We don't have any tests for ai-drv-server, so disable the check.
  #
  # TODO: Add tests
  doCheck = false;

  pythonImportsCheck = [
    "ai_drv_server"
  ];
}
