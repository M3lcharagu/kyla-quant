# Mac upgrade research note

## Supplied research facts

The supplied research identifies the following as a legitimate full installer candidate for OpenCore Legacy Patcher (OCLP):

- macOS Monterey **12.7.6**
- Build **21H1320**
- Product ID **062-40406-A**
- `InstallAssistant.pkg` obtained from **https://swcdn.apple.com**

The supplied research describes Monterey as safer and lighter than Ventura for the 2012 **MacBookPro9,2**. Ventura is described as possible with root patches. These descriptions are research inputs, not a guarantee for a particular machine, installation, driver, patch, or workload.

## Plan and operating context

This is **weekend work**, not an immediate change to the active environment. **KYLA continues running on Catalina meanwhile.** The repository change documents a possible upgrade path only; it does not record that an upgrade was performed.

## Safety and verification gates

Before any upgrade work:

1. Verify the installer identity, version, build, product ID, and source. Use the exact Apple content-delivery source recorded here: **https://swcdn.apple.com**. Do not assume that a similarly named package is authentic or complete.
2. Verify current, restorable backups before modifying the Mac. Keep a recovery path available.
3. Verify the exact MacBookPro9,2 hardware state, OCLP support, patch requirements, storage, and rollback/recovery procedure.
4. Verify Monterey installation and post-install root-patch steps separately from Ventura steps. Do not treat “possible with root patches” as proof that Ventura is the safer choice.
5. Confirm the installer and OCLP workflow on the actual machine before committing to the weekend window.

The installer/source checks, backup checks, hardware checks, and OCLP procedure are steps requiring verification. They are not reported as completed here.

## Status

No macOS upgrade was performed as part of this documentation commit. Until the gates above are satisfied, retain Catalina as the running environment and treat Monterey as the proposed, research-backed candidate rather than an executed change.
