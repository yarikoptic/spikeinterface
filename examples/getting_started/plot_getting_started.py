"""
Getting started with SpikeInterface
===================================

In this introductory example, you will see how to use the :code:`spikeinterface` to perform a full electrophysiology analysis.
We will first create some simulated data, and we will then perform some pre-processing, run a couple of spike sorting
algorithms, inspect and validate the results, export to Phy, and compare spike sorters.

"""

##############################################################################
# Let's first import the :code:`spikeinterface` package.
# We can either import the whole package:

import spikeinterface as si

##############################################################################
# or import the different submodules separately (preferred). There are 5 modules
# which correspond to 5 separate packages:
#
# - :code:`extractors` : file IO and probe handling
# - :code:`toolkit` : processing toolkit for pre-, post-processing, validation, and automatic curation
# - :code:`sorters` : Python wrappers of spike sorters
# - :code:`comparison` : comparison of spike sorting output
# - :code:`widgets` : visualization


import spikeinterface.extractors as se
import spikeinterface.toolkit as st
import spikeinterface.sorters as ss
import spikeinterface.comparison as sc
import spikeinterface.widgets as sw

##############################################################################
# First, let's create a toy example with the :code:`extractors` module:

recording, sorting_true = se.example_datasets.toy_example(duration=10, num_channels=4, seed=0)

##############################################################################
# :code:`recording` is a :code:`RecordingExtractor` object, which extracts information about channel ids, channel locations
# (if present), the sampling frequency of the recording, and the extracellular  traces. :code:`sorting_true` is a
# :code:`SortingExtractor` object, which contains information about spike-sorting related information,  including unit ids,
# spike trains, etc. Since the data are simulated, :code:`sorting_true` has ground-truth information of the spiking
# activity of each unit.
#
# Let's use the :code:`widgets` module to visualize the traces and the raster plots.

w_ts = sw.plot_timeseries(recording, trange=[0,5])
w_rs = sw.plot_rasters(sorting_true, trange=[0,5])

##############################################################################
# This is how you retrieve info from a :code:`RecordingExtractor`...

channel_ids = recording.get_channel_ids()
fs = recording.get_sampling_frequency()
num_chan = recording.get_num_channels()

print('Channel ids:', channel_ids)
print('Sampling frequency:', fs)
print('Number of channels:', num_chan)

##############################################################################
# ...and a :code:`SortingExtractor`
unit_ids = sorting_true.get_unit_ids()
spike_train = sorting_true.get_unit_spike_train(unit_id=unit_ids[0])

print('Unit ids:', unit_ids)
print('Spike train of first unit:', spike_train)

##################################################################
# Optionally, you can load probe information using a '.prb' file. For example, this is the content of
# :code:`custom_probe.prb`:
#
# .. parsed-literal::
#     channel_groups = {
#         0: {
#             'channels': [1, 0],
#             'geometry': [[0, 0], [0, 1]],
#             'label': ['first_channel', 'second_channel'],
#         },
#         1: {
#             'channels': [2, 3],
#             'geometry': [[3,0], [3,1]],
#             'label': ['third_channel', 'fourth_channel'],
#         }
#     }
#
# The '.prb' file uses python-dictionary syntax. With probe files you can change the order of the channels, load 'group'
# properties, 'location' properties (using the  'geometry' or 'location' keys, and any other arbitrary information
# (e.g. 'labels'). All information can be specified as lists (same number of elements of corresponding 'channels' in
# 'channel_group', or dictionaries with the channel id as key and the property as value (e.g. 'labels':
# {1: 'first_channel', 0: 'second_channel'})
#
# You can load the probe file using the :code:`load_probe_file` function in the RecordingExtractor.
# **IMPORTANT**: The :code:`load_probe_file` function returns a ***new** :code:`RecordingExtractor` object and it is
# not performed in-place:

recording_prb = recording.load_probe_file('custom_probe.prb')
print('Channel ids:', recording_prb.get_channel_ids())
print('Loaded properties', recording_prb.get_shared_channel_property_names())
print('Label of channel 0:', recording_prb.get_channel_property(channel_id=0, property_name='label'))

# 'group' and 'location' can be returned as lists:
print(recording_prb.get_channel_groups())
print(recording_prb.get_channel_locations())


##############################################################################
# Using the :code:`toolkit`, you can perform pre-processing on the recordings. Each pre-processing function also returns
# a :code:`RecordingExtractor`, which makes it easy to build pipelines. Here, we filter the recording and apply common
# median reference (CMR)

recording_f = st.preprocessing.bandpass_filter(recording, freq_min=300, freq_max=6000)
recording_cmr = st.preprocessing.common_reference(recording_f, reference='median')

##############################################################################
# Now you are ready to spikesort using the :code:`sorters` module!
# Let's first check which sorters are implemented and which are installed

print('Available sorters', ss.available_sorters())
print('Installed sorters', ss.installed_sorter_list)

##############################################################################
# The :code:`ss.installed_sorter_list` will list the sorters installed in the machine. Each spike sorter
# is implemented as a class. We can see we have Klusta and Mountainsort4 installed.
# Spike sorters come with a set of parameters that users can change. The available parameters are dictionaries and
# can be accessed with:

print(ss.get_default_params('mountainsort4'))
print(ss.get_default_params('klusta'))

##############################################################################
# Let's run mountainsort4 and change one of the parameter, the detection_threshold:

sorting_MS4 = ss.run_mountainsort4(recording=recording_cmr, detect_threshold=6)

##############################################################################
# Alternatively we can pass full dictionary containing the parameters:

ms4_params = ss.get_default_params('mountainsort4')
ms4_params['detect_threshold'] = 4
ms4_params['curation'] = False

# parameters set by params dictionary
sorting_MS4_2 = ss.run_mountainsort4(recording=recording, **ms4_params)

##############################################################################
# Let's run Klusta as well, with default parameters:

sorting_KL = ss.run_klusta(recording=recording_cmr)

##############################################################################
# The :code:`sorting_MS4` and :code:`sorting_MS4` are :code:`SortingExtractor` objects. We can print the units found using:

print('Units found by Mountainsort4:', sorting_MS4.get_unit_ids())
print('Units found by Klusta:', sorting_KL.get_unit_ids())


##############################################################################
# Once we have paired :code:`RecordingExtractor` and :code:`SortingExtractor` objects we can post-process, validate, and curate the
# results. With the :code:`toolkit.postprocessing` submodule, one can, for example, get waveforms, templates, maximum
# channels, PCA scores, or export the data to Phy. `Phy <https://github.com/cortex-lab/phy>`_ is a GUI for manual curation of the spike sorting output.
# To export to phy you can run:

st.postprocessing.export_to_phy(recording, sorting_KL, output_folder='phy')

##############################################################################
# Then you can run the template-gui with: :code:`phy template-gui phy/params.py` and manually curate the results.
#
# Validation of spike sorting output is very important. The :code:`toolkit.validation` module implements several quality
# metrics to assess the goodness of sorted units. Among those, for example, are signal-to-noise ratio, ISI violation
# ratio, isolation distance, and many more.

snrs = st.validation.compute_snrs(sorting_KL, recording_cmr)
isi_violations = st.validation.compute_isi_violations(sorting_KL)
isolations = st.validation.compute_isolation_distances(sorting_KL, recording)

print('SNR', snrs)
print('ISI violation ratios', isi_violations)
print('Isolation distances', isolations)

##############################################################################
# Quality metrics can be also used to automatically curate the spike sorting output. For example, you can select
# sorted units with a SNR above a certain threshold:

sorting_curated_snr = st.curation.threshold_snr(sorting_KL, recording, threshold=5)
snrs_above = st.validation.compute_snrs(sorting_curated_snr, recording_cmr)

print('Curated SNR', snrs_above)

##############################################################################
# The final part of this tutorial deals with comparing spike sorting outputs.
# We can either (1) compare the spike sorting results with the ground-truth sorting :code:`sorting_true`, (2) compare
# the output of two (Klusta and Mountainsor4), or (3) compare the output of multiple sorters:

comp_gt_KL = sc.compare_sorter_to_ground_truth(gt_sorting=sorting_true, tested_sorting=sorting_KL)
comp_KL_MS4 = sc.compare_two_sorters(sorting1=sorting_KL, sorting2=sorting_MS4)
comp_multi = sc.compare_multiple_sorters(sorting_list=[sorting_MS4, sorting_KL],
                                         name_list=['klusta', 'ms4'])


##############################################################################
# When comparing with a ground-truth sorting extractor (1), you can get the sorting performance and plot a confusion
# matrix

comp_gt_KL.get_performance()
w_conf = sw.plot_confusion_matrix(comp_gt_KL)

##############################################################################
# When comparing two sorters (2), we can see the matching of units between sorters. For example, this is how to extract
# the unit ids of Mountainsort4 (sorting2) mapped to the units of Klusta (sorting1). Units which are not mapped has -1
# as unit id.

mapped_units = comp_KL_MS4.get_mapped_sorting1().get_mapped_unit_ids()

print('Klusta units:', sorting_KL.get_unit_ids())
print('Mapped Mountainsort4 units:', mapped_units)

##############################################################################
# When comparing multiple sorters (3), you can extract a :code:`SortingExtractor` object with units in agreement
# between sorters. You can also plot a graph showing how the units are matched between the sorters.

sorting_agreement = comp_multi.get_agreement_sorting(minimum_matching=2)

print('Units in agreement between Klusta and Mountainsort4:', sorting_agreement.get_unit_ids())

w_multi = sw.plot_multicomp_graph(comp_multi)
