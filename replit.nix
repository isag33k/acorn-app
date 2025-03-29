{pkgs}: {
  deps = [
    pkgs.iproute2
    pkgs.gh
    pkgs.openssh
    pkgs.postgresql
    pkgs.openssl
  ];
}
