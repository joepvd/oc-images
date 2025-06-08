# oc-images: List properties and diffs of image collections

Openshift has two related concepts: ImageSteams and Payloads. Some ImageStreams feed in to
a payload. The information about the contents of these entities requires some mechanics to
get to.

This cli application lets one compare payload and imagestream content. The info is retrieved
through `oc`, and it is expected that oc:
- has access to the relevant image registries
- is currently pointing to the right cluster that has the image streams
- the account has access to see them

## Usage

Some example use of `list`:

```
$ oc images list ocp-s390x/4.19-art-latest-s390x --name pod --nvr
openshift-enterprise-pod-container-v4.19.0-202505210330.p0.g375cd1b.assembly.stream.el9

$ oc images list --filter ovn --nvr quay.io/openshift-release-dev/ocp-release:4.19.0-ec.4-x86_64
ose-ovn-kubernetes-container-v4.19.0-202503260216.p0.g12b33c1.assembly.stream.el9
ovn-kubernetes-microshift-container-v4.19.0-202503251208.p0.g12b33c1.assembly.stream.el9

$ time oc images list --nvr quay.io/openshift-release-dev/ocp-release:4.19.0-ec.4-x86_64 | wc -l
189

real	0m6.828s
```

Example use of `diff`:

With payloads:
```
oc images diff quay.io/openshift-release-dev/ocp-release:4.18.2-x86_64 quay.io/openshift-release-dev/ocp-release:4.18.3-x86_64
```

Mixing payload and imagestream:
```
oc images diff quay.io/openshift-release-dev/ocp-release:4.18.2-x86_64 4.18-art-assembly-4.18.3
```

See if release controller will create a new nightly after the current one is done testing:
```
oc images diff registry.ci.openshift.org/ocp/release:4.20.0-0.nightly-2025-06-06-044542 4.20-art-latest
```

## On `collection` arguments
Openshift has two similar concepts. There are _release payloads_, and _imageStreams_.
A release payload is a Cluster Version Operator (CVO) image, where `oc` has layered references
to images contained in the CVO, alongside the manifests that instruct how to run the payload
operators. The "related images" in a release payload is somewhat tied to an ImageStream.

ImageStreams are a collection of images with a name and a pullspec. Payloads typically get constructed
with reference to such an imagestream.

This application takes positional arguments for these image collections, and makes educated guesses
what the user means. These are taken as payloads:

### Specify as payload

This is straightforward: Paste the resource you would use in `oc adm release info`:

```
registry.ci.openshift.org/ocp/release:4.20.0-0.nightly-2025-06-06-044542 
quay.io/openshift-release-dev/ocp-release:4.18.2-x86_64 
quay.io/openshift-release-dev/ocp-release:4.19.0-rc.5-s390x
```

### Specify by imagestream
These are literal imageStreams that are interpreted correctly:

| argument                                   | comment                                 |
|--------------------------------------------|-----------------------------------------|
| `4.19-art-latest`                          | x86\_64 is assumed                      |
| `4.17-art-assembly-4.17-3`                 | Named assembly                          |
| `4.17-art-assembly-4.17-3-s390x`           | Named assembly for funny arch           |
| `ocp-arm64/4.17-art-assembly-4.17-3-arm64` | Named assembly for funny arch           |
| `ocp/4.19-art-latest`                      | Explicitly specify namespace before `/` |
| `ocp-s390x/4.19-art-latest-s390x`          | Fully qualified funny arch              |
| `4.17-art-latest-ppc64le`                  | Namespace is assumed                    |
| `4.17-art-assembly-art123`                 | Custom assemblies also work             |


### Specify by assembly

ImageStreams for an assembly are always prepended with the OCP-ystream they
are relevant for. For zstream releases, the entries in `releases.yml` have this
OCP ystream embedded. For ECs, RCs, and custom assemblies, this is not the case.
So prepend the ystream before the actual name in `releases.yml`, so that:


| Assembly name | Accepted argument | ImageStream                         |
|---------------|-------------------|-------------------------------------|
| `4.19.3`      | `4.19.3`          | `ocp/4.19-art-assembly-4.19.3`      |
| `rc.5`        | `4.19-rc.5`       | `ocp/4.19-art-assembly-4.19.0-rc.5` |
| `art123`      | `4.12-art123`     | `ocp/4.12-art-assembly-4.12-art123` |
| `stream`      | `4.12-stream`     | `ocp/4.12-art-latest`               |
| `stream`      | `4.20-latest`     | `ocp/4.20-art-latest`               |


## Installation
```
git clone https://github.com/joepvd/oc-images.git
cd oc-images
make venv
ln -s "$(pwd)"/.venv/bin/oc-images ~/.local/bin/oc-images
```

## BUGS
- rhel-coreos and rhel-coreos-extensions images are not being reported well
- Would be nice with a helper function, so one can specify an assembly name
  and the image stream name will be guessed
- The report is very wide for the payload diff options. Alternative reports
  might be helpful
- Would be good to be able to specify other attributes for the diff
