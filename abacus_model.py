from dp.launching.typing import BaseModel, Field
from dp.launching.typing import InputFilePath, OutputDirectory, InputMaterialFilePath
from dp.launching.typing import Int, Float, List, Enum, String, Dict, Boolean
from dp.launching.typing.addon.sysmbol import Equal
import dp.launching.typing.addon.ui as ui
from dp.launching.typing import (
    BohriumUsername, 
    BohriumTicket, 
    BohriumProjectId, 
    BohriumJobType,
    BohriumMachineType,
    BohriumPlatform
)
from dp.launching.typing import (
    DflowArgoAPIServer, DflowK8sAPIServer,
    DflowAccessToken, DflowStorageEndpoint,
    DflowStorageRepository, DflowLabels
)
from dp.launching.cli import (
    SubParser,
    default_minimal_exception_handler,
    run_sp_and_exit,
)

inter_group = ui.Group('Interaction Type', 'Define interatomic description')
relax_group = ui.Group('Relaxation Parameters', 'Define Relaxation Parameters')
eos_group = ui.Group('Equation of State (EOS)', 'Equation of State (EOS)')
elastic_group = ui.Group('Elastic Const & Moduli', 'Elastic const & moduli')
surface_group = ui.Group('Surface Formation Energy', 'Surface Formation Energy')
interstitial_group = ui.Group('Interstitial Formation Energy', 'Interstitial Formation Energy')
vacancy_group = ui.Group('Vacancy Formation Energy', 'Vacancy Formation Energy')
gamma_group = ui.Group('GSFE Curve (Gamma Line)', 'GSFE Curve (Gamma Line)')
phonon_group = ui.Group('Phonon Spectra', 'Phonon Spectra')


class InjectConfig(BaseModel):
    # Bohrium config
    bohrium_username: BohriumUsername
    bohrium_ticket: BohriumTicket
    bohrium_project_id: BohriumProjectId
    bohrium_job_type: BohriumJobType = Field(default=BohriumJobType.CONTAINER)
    bohrium_machine_type: BohriumMachineType = Field(default=BohriumMachineType.C8_M31_1__NVIDIA_T4)
    bohrium_platform: BohriumPlatform = Field(default=BohriumPlatform.ALI)

    # dflow config
    dflow_labels: DflowLabels
    dflow_argo_api_server: DflowArgoAPIServer
    dflow_k8s_api_server: DflowK8sAPIServer
    dflow_access_token: DflowAccessToken
    dflow_storage_endpoint: DflowStorageEndpoint
    dflow_storage_repository: DflowStorageRepository


class UploadFiles(BaseModel):
    configurations: List[InputMaterialFilePath] = \
        Field(..., description='Configuration POSCAR to be tested (name differently for multiple files)')
    input: InputFilePath = \
        Field(..., description='ABACUS INPUT file for energy minimization', )
    potentials: List[InputFilePath] = \
        Field(..., description='ABACUS potential file list (name differently for multiple element types)', )
    orbfiles: List[InputFilePath] = \
        Field(..., description='ABACUS orbital file list (name differently for multiple element types)', )
    deepks: List[InputFilePath] = \
        Field(None, description='DeepKS model', )
    parameter_files: List[InputFilePath] = \
        Field(None, ftypes=['json'], max_file_count=2,
            description='(Optional) Specify parameter `JSON` files for APEX to override the default settings,\
               (Do not upload if want to do setting manually in the later UI page)',
        )


class GlobalConfig(BaseModel):
    abacus_image_name: String = Field(
        default="registry.dp.tech/dptech/abacus:3.2.3", 
        description='ABACUS image address for DFT calculation'
    )
    abacus_run_command: String = Field(
        default="mpirun -n 16 abacus", 
        description='ABACUS run command'
    )
    apex_image_name: String = Field(
        default="registry.dp.tech/dptech/prod-11045/apex-dependency:1.2.0", 
        description='Image address including dependencies for APEX to run'
    )
    scass_type: String = Field(
        default="c16_m32_cpu", 
        description='Bohrium machine node type for ABACUS calculation'
    )
    group_size: Int = Field(
        default=1,
        ge=1,
        description='Number of tasks per parallel run group'
    )
    pool_size: Int = Field(
        default=1,
        ge=1,
        description='For multi tasks per parallel group, the pool size of multiprocessing pool to handle each task (1 for serial, -1 for infinity)'
    )



@inter_group
class InterOptions(BaseModel):
    potential_map: Dict[String, String] = Field(
        default={'H': 'H.PBE.UPF'},
        description="Potential files mapping (Key for element name (H, He ...); value for name of potential file: H.PBE.UPF, He.PBE.UPF ...)"
    )
    orbfile_map: Dict[String, String] = Field(
        default={'H': 'H.orb'},
        description="Orbital files mapping (Key for element name (H, He ...); value for name of input ORB file: H.orb, He.orb ...)"
    )
    deepks_map: Dict[String, String] = Field(
        None,
        description="DeepKS model files mapping (Key for element name (H, He ...); value for name of input DeepKS model file: H.deepks, He.deepks ...)"
    )



@relax_group
class RelaxationParameters(BaseModel):
    specify_relax_input: Dict[String, String] = Field(
        default=None,
        description='Specify ABACUS INPUT settings for relaxation'
    )
    relax_pos: Boolean = Field(
        default=True,
        description='Relax atom positions'
    )
    relax_shape: Boolean = Field(
        default=True,
        description='Relax unit cell shape'
    )
    relax_vol: Boolean = Field(
        default=True,
        description='Relax unit cell volume'
    )
    k_points: List[Int] = Field(
        default=None,
        description='K-point mesh for relaxation'
    )


class CalTypeOptions(String, Enum):
    relaxation = 'relaxation'
    static = 'static'


@eos_group
class EOSOptions(BaseModel):
    select_eos: Boolean = Field(default=False, description='Do EOS exploration')


@eos_group
@ui.Visible(EOSOptions, "select_eos", Equal, True)
class EOSParameters(BaseModel):
    custom_eos_calc: Boolean = Field(
        default=False,
        description='Customize advanced ABACUS settings for EOS calculation'
    )
    eos_cal_type: CalTypeOptions = Field(
        default=CalTypeOptions.relaxation,
        render_type="radio",
        description='Type of DFT calculation'
    )
    vol_start: Float = Field(
        default=0.8,
        gt=0,
        description='Starting volume fraction'
    )
    vol_end: Float = Field(
        default=1.2,
        gt=0,
        description='End volume fraction'
    )
    vol_step: Float = Field(
        default=0.05,
        gt=0,
        description='Volume fraction step'
    )
    vol_abs: Boolean = Field(
        default=False,
        description='If is absolute volume'
    )


@eos_group
@ui.Visible(EOSParameters, "custom_eos_calc", Equal, True)
class EOSAdvance(BaseModel):
    specify_eos_input: Dict[String, String] = Field(
        default=None,
        description='Specify ABACUS INPUT settings for EOS calculation'
    )
    eos_relax_pos: Boolean = Field(
        default=False,
        description='Relax atom positions'
    )
    eos_relax_shape: Boolean = Field(
        default=False,
        description='Relax unit cell shape'
    )
    eos_relax_vol: Boolean = Field(
        default=False,
        description='Relax unit cell volume'
    )
    eos_k_points: List[Int] = Field(
        default=None,
        description='K-point mesh for EOS calculation'
    )
    eos_input: String = Field(
        default=None,
        format="multi-line",
        description='Specify INPUT for EOS calculation'
    )

class ModulusTypeOptions(String, Enum):
    voigt = 'voigt'
    reuss = 'reuss'
    vrh = 'vrh'

@elastic_group
class ElasticOptions(BaseModel):
    select_elastic: Boolean = Field(default=False, description='Do elastic property exploration')


@elastic_group
@ui.Visible(ElasticOptions, "select_elastic", Equal, True)
class ElasticParameters(BaseModel):
    custom_elastic_calc: Boolean = Field(
        default=False,
        description='Customize advanced ABACUS settings for elastic property calculation'
    )
    elastic_cal_type: CalTypeOptions = Field(
        default=CalTypeOptions.relaxation,
        render_type="radio",
        description='Type of DFT calculation'
    )
    norm_deform: Float = Field(
        default=0.01,
        gt=0,
        description='Normal deformation'
    )
    shear_deform: Float = Field(
        default=0.01,
        gt=0,
        description='Shear deformation'
    )
    conventional: Boolean = Field(
        default=False,
        description='Transform to conventional cell'
    )
    ieee: Boolean = Field(
        default=False,
        description='Apply ieee standard transformation'
    )
    modulus_type: ModulusTypeOptions = Field(
        default=ModulusTypeOptions.vrh,
        description='Method of modulus approximation'
    )


@elastic_group
@ui.Visible(ElasticParameters, "custom_elastic_calc", Equal, True)
class ElasticAdvance(BaseModel):
    specify_elastic_input: Dict[String, String] = Field(
        default=None,
        description='Specify ABACUS INPUT settings for elastic property calculation'
    )
    elastic_relax_pos: Boolean = Field(
        default=True,
        description='Relax atom positions'
    )
    elastic_relax_shape: Boolean = Field(
        default=False,
        description='Relax unit cell shape'
    )
    elastic_relax_vol: Boolean = Field(
        default=False,
        description='Relax unit cell volume'
    )
    elastic_k_points: List[Int] = Field(
        default=None,
        description='K-point mesh for elastic property calculation'
    )
    elastic_input: String = Field(
        default=None,
        format="multi-line",
        description='Specify INPUT for elastic property calculation'
    )


@surface_group
class SurfaceOptions(BaseModel):
    select_surface: Boolean = Field(default=False, description='Do surface formation energy exploration')


@surface_group
@ui.Visible(SurfaceOptions, "select_surface", Equal, True)
class SurfaceParameters(BaseModel):
    custom_surface_calc: Boolean = Field(
        default=False,
        description='Customize advanced ABACUS settings for surface formation energy calculation'
    )
    surface_cal_type: CalTypeOptions = Field(
        default=CalTypeOptions.relaxation,
        render_type="radio",
        description='Type of DFT calculation'
    )
    max_miller: Int = Field(
        default=2,
        gt=0,
        description='Maximum searched Miller index'
    )
    min_slab_size: Float = Field(
        default=50,
        gt=0,
        description='Minimum slab thickness in Angstrom'
    )
    min_vacuum_size: Float = Field(
        default=20,
        ge=0,
        description='Minimum vacuum layer thickness in Angstrom'
    )
    pert_xz: Float = Field(
        default=0.01,
        ge=0,
        description='Perturbation in xz plane'
    )


@surface_group
@ui.Visible(SurfaceParameters, "custom_surface_calc", Equal, True)
class SurfaceAdvance(BaseModel):
    specify_surface_input: Dict[String, String] = Field(
        default=None,
        description='Specify ABACUS INPUT settings for surface formation energy calculation'
    )
    surface_relax_pos: Boolean = Field(
        default=False,
        description='Relax atom positions'
    )
    surface_relax_shape: Boolean = Field(
        default=False,
        description='Relax unit cell shape'
    )
    surface_relax_vol: Boolean = Field(
        default=False,
        description='Relax unit cell volume'
    )
    surface_k_points: List[Int] = Field(
        default=None,
        description='K-point mesh for surface formation energy calculation'
    )
    surface_input: String = Field(
        default=None,
        format="multi-line",
        description='Specify INPUT for surface formation energy calculation'
    )


@interstitial_group
class InterstitialOptions(BaseModel):
    select_interstitial: Boolean = Field(default=False, description='Do interstitial formation energy exploration')


@interstitial_group
@ui.Visible(InterstitialOptions, "select_interstitial", Equal, True)
class InterstitialParameters(BaseModel):
    custom_interstitial_calc: Boolean = Field(
        default=False,
        description='Customize advanced LAMMPS settings for interstitial formation energy calculation'
    )
    interstitial_cal_type: CalTypeOptions = Field(
        default=CalTypeOptions.relaxation,
        render_type="radio",
        description='Type of MD calculation'
    )
    interstitial_supercell_size: List[Int] = Field(
        default=[2, 2, 2],
        description='Supercell size for interstitial calculation (max 3 integers allowed)'
    )
    insert_ele: String = Field(
        default="H",
        description='Elemen to be inserted'
    )


@interstitial_group
@ui.Visible(InterstitialParameters, "custom_interstitial_calc", Equal, True)
class InterstitialAdvance(BaseModel):
    specify_interstitial_input: Dict[String, String] = Field(
        default=None,
        description='Specify LAMMPS settings for interstitial formation energy calculation'
    )
    interstitial_relax_pos: Boolean = Field(
        default=True,
        description='Relax atom positions'
    )
    interstitial_relax_shape: Boolean = Field(
        default=True,
        description='Relax unit cell shape'
    )
    interstitial_relax_vol: Boolean = Field(
        default=True,
        description='Relax unit cell volume'
    )
    interstitial_k_points: List[Int] = Field(
        default=None,
        description='K-point mesh for interstitial calculation'
    )
    interstitial_input: String = Field(
        default=None,
        format="multi-line",
        description='Specify INPUT for interstitial MD'
    )


@vacancy_group
class VacancyOptions(BaseModel):
    select_vacancy: Boolean = Field(default=False, description='Do vacancy formation energy exploration')


@vacancy_group
@ui.Visible(VacancyOptions, "select_vacancy", Equal, True)
class VacancyParameters(BaseModel):
    custom_vacancy_calc: Boolean = Field(
        default=False,
        description='Customize advanced LAMMPS settings for vacancy formation energy calculation'
    )
    vacancy_cal_type: CalTypeOptions = Field(
        default=CalTypeOptions.relaxation,
        render_type="radio",
        description='Type of MD calculation'
    )
    vacancy_supercell_size: List[Int] = Field(
        default=[2, 2, 2],
        description='Supercell size for vacancy calculation (max 3 integers allowed)'
    )


@vacancy_group
@ui.Visible(VacancyParameters, "custom_vacancy_calc", Equal, True)
class VacancyAdvance(BaseModel):
    specify_vacancy_input: Dict[String, String] = Field(
        default=None,
        description='Specify LAMMPS settings for vacancy formation energy calculation'
    )
    vacancy_relax_pos: Boolean = Field(
        default=True,
        description='Relax atom positions'
    )
    vacancy_relax_shape: Boolean = Field(
        default=False,
        description='Relax unit cell shape'
    )
    vacancy_relax_vol: Boolean = Field(
        default=False,
        description='Relax unit cell volume'
    )
    vacancy_k_points: List[Int] = Field(
        default=None,
        description='K-point mesh for vacancy calculation'
    )
    vacancy_input: String = Field(
        default=None,
        format="multi-line",
        description='Specify INPUT for vacancy MD'
    )


@gamma_group
class GammaOptions(BaseModel):
    select_gamma: Boolean = Field(default=False, description='Do GSFE curve (Gamma line) exploration')


@gamma_group
@ui.Visible(GammaOptions, "select_gamma", Equal, True)
class GammaParameters(BaseModel):
    custom_gamma_calc: Boolean = Field(
        default=False,
        description='Customize advanced LAMMPS settings for GSFE curve (Gamma line) calculation'
    )
    gamma_cal_type: CalTypeOptions = Field(
        default=CalTypeOptions.relaxation,
        render_type="radio",
        description='Type of MD calculation'
    )
    plane_miller: List[Int] = Field(
        default=[1, 1, 1],
        description='Miller index of gamma slab surface (max 4 integers allowed)'
    )
    slip_direction: List[Int] = Field(
        default=[-1, 1, 0],
        description='Slip direction of gamma slab surface (max 4 integers allowed)'
    )
    slip_length: List[Float] = Field(None,
        description='(Optional) Slip length of gamma slab surface (max 3 floats allowed)'
    )
    plane_shift: Float = Field(
        default=0,
        description='Shift of slip plane along the slab z direction'
    )
    gamma_n_steps: Int = Field(
        default=10,
        gt=0,
        description='Number of slip steps'
    )
    gamma_supercell_size: List[Int] = Field(
        default=[1, 1, 5],
        description='Supercell size for gamma calculation (max 3 integers allowed)'
    )
    gamma_vacuum_size: Float = Field(
        default=0,
        ge=0,
        description='Vacuum layer thickness in Angstrom'
    )
    add_fix_x: Boolean = Field(
        default=True,
        description='Fix atom along x direction'
    )
    add_fix_y: Boolean = Field(
        default=True,
        description='Fix atom along y direction'
    )
    add_fix_z: Boolean = Field(
        default=False,
        description='Fix atom along z direction'
    )


@gamma_group
@ui.Visible(GammaParameters, "custom_gamma_calc", Equal, True)
class GammaAdvance(BaseModel):
    specify_gamma_input: Dict[String, String] = Field(
        default=None,
        description='Specify LAMMPS settings for GSFE curve (Gamma line) calculation'
    )
    gamma_relax_pos: Boolean = Field(
        default=True,
        description='Relax atom positions'
    )
    gamma_relax_shape: Boolean = Field(
        default=False,
        description='Relax unit cell shape'
    )
    gamma_relax_vol: Boolean = Field(
        default=False,
        description='Relax unit cell volume'
    )
    gamma_k_points: List[Int] = Field(
        default=None,
        description='K-point mesh for GSFE curve (Gamma line) calculation'
    )
    gamma_input: String = Field(
        default=None,
        format="multi-line",
        description='Specify INPUT for GSFE curve (Gamma line) MD'
    )


@phonon_group
class PhononOptions(BaseModel):
    select_phonon: Boolean = Field(default=False, description='Do phonon spectra exploration')



@phonon_group
@ui.Visible(PhononOptions, "select_phonon", Equal, True)
class PhononParameters(BaseModel):
    specify_phonopy_settings: Boolean = Field(
        default=False,
        description='Specify phonopy settings directly for phonon spectra calculation'
    )
    primitive_cell: Boolean = Field(
        default=False,
        description='Use primitive cell for phonon calculation'
    )
    phonon_supercell_size: List[Int] = Field(
        default=[2, 2, 2],
        description='Supercell size for phonon calculation (max 3 integers allowed)'
    )
    seekpath_from_original: Boolean = Field(
        default=False,
        description='Seekpath search by original cell'
    )


@phonon_group
@ui.Visible(PhononParameters, "specify_phonopy_settings", Equal, True)
class PhononAdvance(BaseModel):
    band: String = Field(None,
        description='(Optional) Phonopy BAND'
    )
    band_labels: String = Field(None,
        description='(Optional) Phonopy BAND_LABELS'
    )
    mesh: String = Field(None,
        description='(Optional) Phonopy MESH'
    )
    primitive_axes: String = Field(None,
        description='(Optional) Phonopy PRIMITIVE_AXES'
    )
    band_points: String = Field(None,
        description='(Optional) Phonopy BAND_POINTS'
    )
    band_connection: Boolean = Field(
        default=True,
        description='Phonopy BAND_CONNECTION'
    )
    phonon_input: String = Field(
        default=None,
        format="multi-line",
        description='ABACUS INPUT instruction for Phonon'
    )


class AbacusModel(
    InjectConfig, 
    UploadFiles, 
    GlobalConfig,
    InterOptions,
    RelaxationParameters,
    EOSOptions,
    EOSParameters,
    EOSAdvance,
    ElasticOptions,
    ElasticParameters,
    ElasticAdvance,
    SurfaceOptions,
    SurfaceParameters,
    SurfaceAdvance,
    InterstitialOptions,
    InterstitialParameters,
    InterstitialAdvance,
    VacancyOptions,
    VacancyParameters,
    VacancyAdvance,
    GammaOptions,
    GammaParameters,
    GammaAdvance,
    PhononOptions,
    PhononParameters,
    PhononAdvance,
    BaseModel
):
    output_directory: OutputDirectory = Field(default='./outputs')

def abacus_runner(opts: AbacusModel):
    pass

if __name__ == "__main__":
    run_sp_and_exit(
        {
            "ABACUS": SubParser(AbacusModel, abacus_runner, "Submit QM workflow using ABACUS"),
        },
        description="APEX workflow submission",
        version="0.1.0",
        exception_handler=default_minimal_exception_handler,
    )
