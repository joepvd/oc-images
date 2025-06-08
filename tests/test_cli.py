import pytest
from click.testing import CliRunner

from oc_images.cli import images


@pytest.mark.functional
class TestCliList:
    def test_list_name_nvr(self):
        runner = CliRunner()
        result = runner.invoke(
            images,
            [
                "list",
                "--name",
                "ironic",
                "quay.io/openshift-release-dev/ocp-release:4.20.0-ec.0-x86_64",
            ],
        )
        assert result.exit_code == 0
        assert (
            "ironic-container-v4.20.0-202504141045.p0.g9de7792.assembly.stream.el9"
            == result.output.strip()
        )

    def test_list_filter_nvr(self):
        runner = CliRunner()
        result = runner.invoke(
            images,
            [
                "list",
                "--filter",
                "ovn",
                "quay.io/openshift-release-dev/ocp-release:4.20.0-ec.0-x86_64",
            ],
        )
        assert result.exit_code == 0
        assert (
            "ose-ovn-kubernetes-container-v4.20.0-202504291213.p0.gf7dd74f.assembly.stream.el9"
            in result.output
        )
        assert (
            "ovn-kubernetes-microshift-container-v4.20.0-202504291213.p0.gf7dd74f.assembly.stream.el9"
            in result.output
        )

    def test_list_filter_name(self):
        runner = CliRunner()
        result = runner.invoke(
            images, ["list", "--filter", "ovn", "--name", "ovn-kubernetes", "payload"]
        )
        assert result.exit_code != 0
        assert (
            "Error: Invalid value: Filter and name cannot both be specified"
            in result.output
        )

    def test_list_is(self):
        runner = CliRunner()
        result = runner.invoke(
            images, ["list", "--name", "ironic", "4.13-art-assembly-4.13.29"]
        )
        assert result.exit_code == 0
        assert (
            "ironic-container-v4.13.0-202312041532.p0.g1585b09.assembly.stream"
            == result.output.strip()
        )

    def test_list_is_s390x(self):
        runner = CliRunner()
        result = runner.invoke(
            images, ["list", "--name", "ironic", "ocp-s390x/4.18.10"]
        )
        assert result.exit_code == 0
        # This is no error, ironic has no s390x build
        assert (
            "openshift-enterprise-pod-container-v4.18.0-202504151633.p0.g97471c6.assembly.stream.el9"
            == result.output.strip()
        )

    def test_list_is_s390x_assembly(self):
        runner = CliRunner()
        result = runner.invoke(
            images,
            [
                "list",
                "--name",
                "cli",
                "ocp-s390x/4.18-art-assembly-4.18.10-s390x",
            ],
        )
        assert result.exit_code == 0
        assert (
            "openshift-enterprise-cli-container-v4.18.0-202504151633.p0.geb9bc9b.assembly.stream.el9"
            == result.output.strip()
        )

    def test_list_is_sha(self):
        runner = CliRunner()
        result = runner.invoke(
            images,
            ["list", "4.18-art-assembly-4.18.3", "--name", "installer", "--pullspec"],
        )
        assert result.exit_code == 0
        assert (
            "ocp-v4.0-art-dev@sha256:4e672082ec967a9de7d149cf5cd7cbd4036425806d75ec6762b974bb3ae26d6d"
            in result.output
        )

    def test_list_payload_sha(self):
        runner = CliRunner()
        result = runner.invoke(
            images,
            [
                "list",
                "--pullspec",
                "quay.io/openshift-release-dev/ocp-release:4.18.3-x86_64",
                "--name",
                "installer",
            ],
        )
        assert result.exit_code == 0
        assert (
            "ocp-v4.0-art-dev@sha256:4e672082ec967a9de7d149cf5cd7cbd4036425806d75ec6762b974bb3ae26d6d"
            in result.output
        )

    def test_list_assembly(self):
        runner = CliRunner()
        result = runner.invoke(
            images,
            ["list", "4.18.5", "--name", "kube-rbac-proxy"],
        )
        assert result.exit_code == 0
        assert (
            "kube-rbac-proxy-container-v4.18.0-202502250302.p0.g526498a.assembly.stream.el9"
            in result.output
        )


@pytest.mark.functional
class TestCliDiff:
    def test_payload_diff(self):
        runner = CliRunner()
        result = runner.invoke(
            images,
            [
                "diff",
                "quay.io/openshift-release-dev/ocp-release:4.18.2-x86_64",
                "quay.io/openshift-release-dev/ocp-release:4.18.3-x86_64",
            ],
        )
        assert result.exit_code == 0
        print(result.output)
        assert (
            "ose-machine-config-operator-container-v4.18.0-202502260503.p0.g8303123.assembly.stream.el9"
            in result.output
        )
        assert (
            "ose-machine-config-operator-container-v4.18.0-202503040202.p0.g7c29816.assembly.stream.el9"
            in result.output
        )
        assert (
            "quay.io/openshift-release-dev/ocp-release:4.18.2-x86_64" in result.output
        )
        assert (
            "quay.io/openshift-release-dev/ocp-release:4.18.3-x86_64" in result.output
        )

    def test_is_payload_diff(self):
        runner = CliRunner()
        result = runner.invoke(
            images,
            [
                "diff",
                "quay.io/openshift-release-dev/ocp-release:4.18.2-x86_64",
                "4.18-art-assembly-4.18.3",
            ],
        )
        assert result.exit_code == 0
        assert (
            "ose-machine-config-operator-container-v4.18.0-202502260503.p0.g8303123.assembly.stream.el9"
            in result.output
        )
        assert (
            "ose-machine-config-operator-container-v4.18.0-202503040202.p0.g7c29816.assembly.stream.el9"
            in result.output
        )
        assert len(result.output.splitlines()) == 16
        assert (
            "quay.io/openshift-release-dev/ocp-release:4.18.2-x86_64" in result.output
        )
        assert " ocp/4.18-art-assembly-4.18.3 " in result.output
        assert "Enlisting difference NVRs" in result.output
        assert "Only in ocp/4.18-art-assembly-4.18.3" in result.output
        assert "azure-service-operator" in result.output
