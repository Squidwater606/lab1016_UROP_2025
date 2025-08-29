'''Determines nonlinearity of SLM-200 phase profile'''
import numpy as np
import scipy.optimize as sp
import matplotlib.pyplot as plt

data_paths = [
    r"C:\Users\rudy_\Documents\SLM_Calibration\SLM\calibration\629nm.txt",
    r"C:\Users\rudy_\Documents\SLM_Calibration\SLM\calibration\632nm.txt",
    r"C:\Users\rudy_\Documents\SLM_Calibration\SLM\calibration\635nm.txt",
    r"C:\Users\rudy_\Documents\SLM_Calibration\SLM\calibration\638nm.txt",
    r"C:\Users\rudy_\Documents\SLM_Calibration\SLM\calibration\641nm.txt"
]

pt_fmts = [
    "b+",
    "gx",
    "r.",
    "co",
    "mv"
]

fit_fmts = [
    "b--",
    "g--",
    "r--",
    "c--",
    "m--"
]

labels = [
    "629nm",
    "632nm",
    "635nm",
    "638nm",
    "641nm"
]

op_wav = np.array([
    629,
    632,
    635,
    638,
    641
])

y_labels = [
    'Intensity (Hz)',
    'FO Correction'
]

x_labels = [
    'Greyscale',
    'Operational Wavelength (nm)'
]

REL_Y_ERR = 0.0012
EPS = 1E-12

def linear_cos_square(x, x0, a, b, c):
    '''Squared cosine with linear phase profile'''
    return a * np.cos(b * (x - x0) ) ** 2 + c

def nonlinear1_cos_square(x, x0, a, b, c, d):
    '''Squared cosine with first order phase correction'''
    return a * (np.cos(d * (x - x0) ** 2 + b * (x - x0)) ** 2) + c

def nonlinear2_cos_square(x, x0, a, b, c, d, e):
    '''Squared cosine with second order phase correction'''
    return a * np.cos(e * (x - x0) ** 3 + d * (x - x0) ** 2 + b * (x - x0)) ** 2 + c

fig, ax1 = plt.subplots(2, 1)
ax2 = ax1[1].twinx()
fig.tight_layout()

nonlinearity1 = np.zeros(5)
nonlinearity2 = np.zeros(5)
err = np.zeros([5, 2])

grey_curve = np.linspace(0, 1023, 1000)

#Plot Phase Profiles
for i in range(1):
    grey, intensity = np.loadtxt(data_paths[i], dtype=float, delimiter='\t', unpack=True)

    ps_guess = grey[np.argmax(intensity[:30])]
    scale_guess = np.max(intensity)
    freq_guess = np.pi / (2 * np.abs(grey[np.argmax(intensity[:30])] - grey[np.argmin(intensity)]))
    i_shift = np.min(intensity)
    p_guess0 = np.array([ps_guess, scale_guess, freq_guess, i_shift])

    ps_lower, ps_upper = ps_guess - 50, ps_guess + 50
    scale_lower, scale_upper = scale_guess - 10 * i_shift, scale_guess + 10 * i_shift
    freq_lower, freq_upper = np.pi / 1023, 2 * freq_guess - np.pi / 1023
    is_lower, is_upper = 0.0, 10 * i_shift
    lower0 = np.array([ps_lower, scale_lower, freq_lower, is_lower])
    upper0 = np.array([ps_upper, scale_upper, freq_upper, is_upper])

    p_optimize0, _ = sp.curve_fit(linear_cos_square,
                        grey, intensity, p0=p_guess0,
                        sigma=REL_Y_ERR*intensity, absolute_sigma=True,
                        bounds=(lower0, upper0))
    print(p_optimize0)

    # p_guess1 = np.append(p_optimize0, 0.0)
    # lower1 = np.append(p_optimize0 - EPS, [-np.inf])
    # upper1 = np.append(p_optimize0 + EPS, [np.inf])

    # p_optimize1, _ = sp.curve_fit(nonlinear1_cos_square,
    #                     grey, intensity, p0=p_guess1,
    #                     sigma=REL_Y_ERR*intensity, absolute_sigma=True,
    #                     bounds=(lower1, upper1))

    # p_guess2 = np.append(p_optimize1, 0.0)
    # lower2 = np.append(p_optimize1 - EPS, [-np.inf])
    # upper2 = np.append(p_optimize1 + EPS, [np.inf])

    # p_optimize2, cov = sp.curve_fit(nonlinear2_cos_square,
    #                     grey, intensity, p0=p_guess2,
    #                     sigma=REL_Y_ERR*intensity, absolute_sigma=True,
    #                     bounds=(lower2, upper2))
    # print(p_optimize2)
    # p_var = np.diag(cov)

    curve_fit = linear_cos_square(grey_curve, *p_optimize0)

    # nonlinearity1[i] = p_optimize2[4] / p_optimize2[2]
    # nonlinearity2[i] = p_optimize2[5] / p_optimize2[2]
    # err[i] = np.array([np.sqrt(p_var[2] + p_var[4]),
    #                 np.sqrt(p_var[2] + p_var[5])])

    ax1[0].errorbar(grey, intensity,
                yerr = REL_Y_ERR * intensity, xerr = 0.5,
                fmt = pt_fmts[i], label = labels[i])
    ax1[0].plot(grey_curve, curve_fit, fit_fmts[i])

for j in range(2):
    ax1[j].grid()
    ax1[j].set_ylabel(y_labels[j], fontsize=11)
    ax1[j].set_xlabel(x_labels[j], fontsize=11)

    ax1[0].legend()
#     ax2.set_ylabel('SO Correction', fontsize=11)

# ax1[1].errorbar(op_wav, nonlinearity1, yerr = err[:,0],
#                 fmt="b+", label='First Order', capsize=10.0)
# ax2.errorbar(op_wav, nonlinearity2, yerr = err[:,1],
#              fmt="mx", label='Second Order', capsize=10.0)
# ax1[1].legend()
# ax2.legend()

plt.show()
