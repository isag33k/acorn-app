{pkgs}: {
  deps = [
    pkgs.jq
    pkgs.glibcLocales
    pkgs.iproute2
    pkgs.gh
    pkgs.openssh
    pkgs.postgresql
    pkgs.openssl
  ];
}
