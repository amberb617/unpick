rule base64_pipe_to_shell {
  meta: severity = "HIGH" description = "base64-decoded data piped into a shell"
  strings: $a = /base64\s+(-d|--decode)\s*\|\s*(ba|z)?sh/
  condition: $a
}
rule zero_width_space {
  meta: severity = "MEDIUM" description = "U+200B zero-width space"
  strings: $a = { E2 80 8B }
  condition: $a
}
rule invalid_tld_domain {
  meta: severity = "LOW" description = "reference to a .invalid domain"
  strings: $a = /[a-z0-9-]+\.invalid/
  condition: $a
}
rule ssh_key_exfil_instruction {
  meta: severity = "HIGH" description = "instruction to read an SSH private key"
  strings: $a = "~/.ssh/id_rsa"
  condition: $a
}
