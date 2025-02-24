{ pkgs, lib, config, inputs, ... }:

{
  # See full reference at https://devenv.sh/reference/options/
  # https://devenv.sh/basics/
  env = {
    STEPUP_DEBUG = "1";
    STEPUP_SYNC_RPC_TIMEOUT = "30";
  };

  # https://devenv.sh/packages/
  packages = with pkgs; [
    #gitFull
    #pre-commit
    # Packages with binaries: take from nix instead of pip
    (python312.withPackages (ps:
    with ps; [
      matplotlib
      numpy
      scipy
      weasyprint
    ]))
    mupdf-headless
  ];

  # https://devenv.sh/languages/
  languages.python = {
    enable = true;
    venv.enable = true;
    venv.requirements = "-e .[dev]";
  };
}
