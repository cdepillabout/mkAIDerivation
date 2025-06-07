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

  setuptoolsCheckPhase = "true";

  doCheck = true;

  pythonImportsCheck = [
    "ai_drv_server"
  ];
}
