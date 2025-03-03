{ pkgs, lib, config, inputs, ... }:

{
  # See full reference at https://devenv.sh/reference/options/
  # https://devenv.sh/basics/
  env = {
    STEPUP_DEBUG = "1";
    STEPUP_SYNC_RPC_TIMEOUT = "30";
  };

  # https://devenv.sh/packages/
  # See https://github.com/cachix/devenv/issues/1264
  packages = with pkgs; [
    stdenv.cc.cc.lib # required by jupyter
    gcc-unwrapped # fix: libstdc++.so.6: cannot open shared object file
    libz # fix for numpy/pandas
    glib # fix for weasyprint
    pango # fix for weasyprint
    fontconfig # fix for weasyprint
  ];

  # https://devenv.sh/languages/
  languages.python = {
    enable = true;
    venv.enable = true;
    venv.requirements = ''
      -e .[dev]
    '';
  };

  env.LD_LIBRARY_PATH = "${pkgs.gcc-unwrapped.lib}/lib64:${pkgs.libz}/lib:${pkgs.glib}/lib:${pkgs.pango}/lib:${pkgs.fontconfig}/lib";
}
