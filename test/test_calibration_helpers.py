#!/usr/bin/python3

import sys
import numpy as np
import numpysane as nps
import copy
import os

# I import the LOCAL mrcal since that's what I'm testing
testdir = os.path.dirname(os.path.realpath(__file__))
sys.path[:0] = f"{testdir}/..",
import mrcal



def optimize( intrinsics,
              extrinsics_rt_fromref,
              frames_rt_toref,
              observations,
              indices_frame_camintrinsics_camextrinsics,
              lensmodel, imagersizes,
              object_spacing, object_width_n, object_height_n,
              pixel_uncertainty_stdev,

              calobject_warp                    = None,
              do_optimize_intrinsic_core        = False,
              do_optimize_intrinsic_distortions = False,
              do_optimize_extrinsics            = False,
              do_optimize_frames                = False,
              do_optimize_calobject_warp        = False,
              skip_outlier_rejection            = True,
              skip_regularization               = False,
              get_covariances                   = False,
              **kwargs):
    r'''Run the optimizer

    Function arguments are read-only. The optimization results, in various
    forms, are returned.

    '''

    intrinsics            = copy.deepcopy(intrinsics)
    extrinsics_rt_fromref = copy.deepcopy(extrinsics_rt_fromref)
    frames_rt_toref       = copy.deepcopy(frames_rt_toref)
    calobject_warp        = copy.deepcopy(calobject_warp)
    observations          = copy.deepcopy(observations)

    solver_context = mrcal.SolverContext()
    stats = mrcal.optimize( intrinsics, extrinsics_rt_fromref, frames_rt_toref, None,
                            observations, indices_frame_camintrinsics_camextrinsics,
                            None, None, lensmodel,
                            calobject_warp              = calobject_warp,
                            imagersizes                 = imagersizes,
                            calibration_object_spacing  = object_spacing,
                            calibration_object_width_n  = object_width_n,
                            calibration_object_height_n = object_height_n,
                            verbose                     = False,

                            observed_pixel_uncertainty  = pixel_uncertainty_stdev,

                            do_optimize_frames                = do_optimize_frames,
                            do_optimize_intrinsic_core        = do_optimize_intrinsic_core,
                            do_optimize_intrinsic_distortions = do_optimize_intrinsic_distortions,
                            do_optimize_extrinsics            = do_optimize_extrinsics,
                            do_optimize_calobject_warp        = do_optimize_calobject_warp,
                            get_covariances                   = get_covariances,
                            skip_regularization               = skip_regularization,
                            skip_outlier_rejection            = skip_outlier_rejection,
                            solver_context                    = solver_context,
                            **kwargs)

    covariance_intrinsics        = stats.get('covariance_intrinsics')
    covariance_extrinsics        = stats.get('covariance_extrinsics')
    covariances_ief              = stats.get('covariances_ief')
    covariances_ief_rotationonly = stats.get('covariances_ief_rotationonly')
    p_packed = solver_context.p().copy()

    return \
        intrinsics, extrinsics_rt_fromref, frames_rt_toref, calobject_warp,   \
        observations[...,2] < 0.0, \
        p_packed, stats['x'], stats['rms_reproj_error__pixels'], \
        covariance_intrinsics, covariance_extrinsics, covariances_ief, covariances_ief_rotationonly, \
        solver_context


def sample_dqref(observations,
                 pixel_uncertainty_stdev,
                 make_outliers = False):

    weight  = observations[...,-1]
    q_noise = np.random.randn(*observations.shape[:-1], 2) * pixel_uncertainty_stdev / nps.mv(nps.cat(weight,weight),0,-1)

    if make_outliers:
        if not hasattr(sample_dqref, 'idx_outliers_ref_flat'):
            NobservedPoints = observations.size // 3
            sample_dqref.idx_outliers_ref_flat = \
                np.random.choice( NobservedPoints,
                                  (NobservedPoints//100,), # 1% outliers
                                  replace = False )
        nps.clump(q_noise, n=3)[sample_dqref.idx_outliers_ref_flat, :] *= 20

    observations_perturbed = observations.copy()
    observations_perturbed[...,:2] += q_noise
    return q_noise, observations_perturbed