{pkgs}: {
  deps = [
    pkgs.glibcLocales
    pkgs.iproute2
    pkgs.gh
    pkgs.openssh
    pkgs.postgresql
    pkgs.openssl
  ];
}
