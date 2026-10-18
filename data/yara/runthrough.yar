// unpick bundled YARA-X rules. Byte-level twins of the built-in checks, so YARA-X can run as an
// independent second opinion. Each rule cites where the pattern comes from.

rule base64_pipe_to_shell {
    meta:
        description = "base64-decoded data piped into a shell"
        severity = "HIGH"
        source = "ClawHavoc lure, Unit 42 https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/"
    strings:
        $a = /base64[ \t]+(-d|-D|--decode)[^\n]{0,200}\|[ \t]*(sudo[ \t]+)?(ba|z)?sh\b/
    condition:
        $a
}

rule download_pipe_to_shell {
    meta:
        description = "download piped straight into a shell"
        severity = "HIGH"
        source = "common installer abuse; ClawHavoc lure"
    strings:
        $a = /\b(curl|wget)\b[^\n|]{0,300}\|[ \t]*(sudo[ \t]+)?(ba|z)?sh\b/
    condition:
        $a
}

rule powershell_download_execute {
    meta:
        description = "PowerShell downloads and runs code"
        severity = "HIGH"
        source = "Windows equivalent of pipe-to-shell"
    strings:
        $a = /\b(iex|Invoke-Expression)\b[^\n]{0,20}\(?[ \t]*(iwr|irm|Invoke-WebRequest|Invoke-RestMethod)/ nocase
        $b = /powershell(\.exe)?[^\n]{0,80}[ \t]-(e|ec|enc|encodedcommand)[ \t]+[A-Za-z0-9+\/=]{16,}/ nocase
    condition:
        any of them
}

rule unicode_tag_characters {
    meta:
        description = "Unicode tag characters (U+E0000..U+E007F): invisible text"
        severity = "HIGH"
        source = "ASCII smuggling via tag characters"
    strings:
        $a = { F3 A0 80 ?? }
        $b = { F3 A0 81 ?? }
    condition:
        any of them
}

rule bidi_controls {
    meta:
        description = "bidirectional control characters (U+202A..U+202E, U+2066..U+2069)"
        severity = "HIGH"
        source = "Rules File Backdoor, Pillar Security 2025; Trojan Source"
    strings:
        $a = { E2 80 AA }
        $b = { E2 80 AB }
        $c = { E2 80 AC }
        $d = { E2 80 AD }
        $e = { E2 80 AE }
        $f = { E2 81 A6 }
        $g = { E2 81 A7 }
        $h = { E2 81 A8 }
        $i = { E2 81 A9 }
    condition:
        any of them
}

rule zero_width_characters {
    meta:
        description = "zero-width characters (U+200B, U+200C, U+2060)"
        severity = "MEDIUM"
        source = "Rules File Backdoor, Pillar Security 2025"
    strings:
        $a = { E2 80 8B }
        $b = { E2 80 8C }
        $c = { E2 81 A0 }
    condition:
        any of them
}

rule ssh_key_read_instruction {
    meta:
        description = "instruction that names an SSH private key"
        severity = "HIGH"
        source = "Invariant Labs tool-poisoning PoC https://github.com/invariantlabs-ai/mcp-injection-experiments"
    strings:
        $a = /~\/\.ssh\/id_(rsa|ed25519|ecdsa)/
        $b = /\.ssh[\/\\]id_(rsa|ed25519|ecdsa)/
    condition:
        any of them
}

rule secrecy_phrase {
    meta:
        description = "tells the model to hide something from the user"
        severity = "HIGH"
        source = "Invariant Labs tool-poisoning PoC"
    strings:
        $a = /(do not|don't|never) (tell|mention|inform|reveal)( this)?( to)? the user/ nocase
    condition:
        $a
}

rule tool_poisoning_markup {
    meta:
        description = "<IMPORTANT> block inside a description"
        severity = "MEDIUM"
        source = "Invariant Labs tool-poisoning PoC"
    strings:
        $a = "<IMPORTANT>" nocase
    condition:
        $a
}

rule paste_site_url {
    meta:
        description = "URL on a paste site or throwaway host"
        severity = "MEDIUM"
        source = "data/paste_domains.txt (subset)"
    strings:
        $a = /https?:\/\/([a-z0-9-]+\.)*(glot\.io|pastebin\.com|paste\.ee|rentry\.co|transfer\.sh|0x0\.st|webhook\.site|ngrok-free\.app|trycloudflare\.com)\b/ nocase
    condition:
        $a
}
