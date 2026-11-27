# Current live application baseline

Prepared from the reviewed production source export plus the verified targeted-live-baseline-20261127 release (80 installed files). Marketing contains the separately exported active marketing release. This is a source/assets snapshot, not a database or server image.

Production verification: all three active site schemas, HTTPS campus/assets and unchanged public catalogue passed; web/workers running. Backup: /home/sisu/.sisu-secrets/merged-production-20261127T003413695757Z.

Automatic institute deletion is excluded. The root removal worker is not installed. The removal-request UI remains present but does not delete hosting/database resources automatically.

No secrets, site_config files, customer uploads, production databases or server credentials are included. Existing repository documentation/tooling outside runtime directories is retained and may describe historical work. This commit does not deploy anything. See docs/FINAL_HANDOVER_20261127.md.
