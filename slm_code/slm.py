'''Piece for Santec SLM-200'''

# Standard imports
import os
import glob
import numpy as np
import ctypes as ct

# Imports for piece
import puzzlepiece as pzp
from pyqtgraph.Qt import QtWidgets

# Imports for SLM
import _slm_win as slm


class SlmError(Exception):
    '''
    SLM not OK.
    '''


class SlmDVI(pzp.Piece):
    '''
    Class for handling Santec SLM-200 interfacing in DVI mode.

    ---Control Sequence---
    -> Toggle Open
    -> Settings
        -> Display Settings
            -> Display Number
            -> Display Info
            -> Toggle Display
        -> Phase Settings
            -> Wavelength
            -> Phase
            -> Set Tuning
    -> Control Display (e.g. Write Contrast)
    -> Toggle Closed

    ---Ensurers---
    _ensure_slm_open :
        Ensures SLM-200 is open.
    _ensure_slm_ready :
        Ensures SLM-200 is not busy.
    _ensure_display_open :
        Ensures display is open.
    _ensure_display_number :
        Ensures display has number.

    ---Attributes---
    handle_close :
        If SLM-200 is open, close.
    custom_layout :
        Shows data currently on display.

    ---Private Params---
    _slm_number : 1
        Assigned number for piece; currently set to 1
        as there is only one SLM needed for setup.
    _bmp_filepath : rstr
        Fixed path for BMP files.
    _data_filepath : rstr
        Fixed path for CSV files.
    '''

    def __init__(self, puzzle):
        super().__init__(puzzle)
        self._display_image = None

    @pzp.piece.ensurer
    def _ensure_slm_open(self):
        if not self.puzzle.debug and not self.params['_slm_open'].value:
            raise SlmError('SLM is not open.')

    @pzp.piece.ensurer
    def _ensure_slm_ready(self):
        if not self.puzzle.debug:
            status = slm.SLM_Ctrl_ReadSU(self._slm_number)
            if status != slm.SLM_OK:
                raise SlmError('SLM is not ready.')

    @pzp.piece.ensurer
    def _ensure_display_open(self):
        if not self.puzzle.debug and not self.params['_display_open'].value:
            raise SlmError('Display is not open.')

    @pzp.piece.ensurer
    def _ensure_display_number(self):
        if not self.puzzle.debug and self.params['Display Number'].value == '':
            raise SlmError('Set Display Number.')

    def handle_close(self, event):
        '''
        If SLM is open, close; if display is open, close display.
        '''

    def custom_layout(self):
        '''
        Shows data currently on display.
        '''

    def define_params(self):
        '''
        ---Puzzlepiece Params---
        _slm_open : bool -> bool
            Discerns whether the SLM-200 has been opened.
        _display_open : bool -> bool
            Discerns whether the display has been opened.
        Display Number : list[int] -> int
            Detects SLM-200 port(s) and returns valid display number(s);
            user then chooses which display they wish to open.
        Display Info : int -> str
            Returns info about the selected display.
        Wavelength: int -> int
            Assigned wavelength of SLM-200.
        Phase : float.3sf -> int
            Assigned phase of SLM-200 (e.g. 2.00 -> 200).
        Contrast : int -> int
            Displays contrast level.
        BMP : -> list[str]
            Returns BMP file from bmp_path.
        Data : -> list[str]
            Returns data file from data_path.
        '''

        pzp.param.checkbox(self, '_slm_open', 0, visible = False)(None)

        pzp.param.checkbox(self, '_display_open', 0, visible=False)(None)

        @pzp.param.dropdown(self, 'Display Number', '', visible=False)
        def display_number(self) -> str:
            '''
            Scans over display ports and compiles list of valid display numbers.
            '''
            if not self.puzzle.debug:

                if not self.params['_display_open'].value:
                    # Create buffers
                    display_width = slm.USHORT()
                    display_height = slm.USHORT()
                    display_name_buffer = ct.create_string_buffer(64)
                    self._display_numbers = []
                    self._display_widths = []
                    self._display_heights = []
                    self._display_names = []

                    # Search for display
                    for display_number in range(1,9):
                        ret = slm.SLM_Disp_Info2(
                                display_number,
                                display_width,
                                display_height,
                                display_name_buffer
                                )

                        if ret == slm.SLM_OK:
                            # mbcs -> unicode
                            display_name = display_name_buffer.value.decode('mbcs').split(',')

                            if display_name[0] == 'LCOS-SLM':
                                # Record valid display information
                                self._display_numbers.append(display_number)
                                self._display_widths.append(display_width)
                                self._display_heights.append(display_height)
                                self._display_names.append(display_name)

                    return self._display_numbers

                raise SlmError('Must close display.')

            return [1, 2, 3, 4, 5, 6, 7, 8]

        @pzp.param.readout(self, 'Display Info', visible=False)
        @self._ensure_display_number
        def display_info(self) -> str: # Test this
            '''
            Returns a string of info about selected display;
            display_name :
                Name of display.
            display_serial :
                Serial number of display.
            display_width :
                Width of display.
            display_height :
                Height of display.
            '''
            # Create format
            fmt = 'Name:\t{}\nSerial:\t{}\nWidth:\t{}\nHeight\t{}'

            if not self.puzzle.debug:

                # Extract display information

                display_number = int(self.params['Display Number'].value)
                display_index = self._display_numbers.index(display_number)

                display_name = self._display_names[display_index][0]
                display_serial = self._display_names[display_index][3]
                width = str(self._display_widths[display_index].value)
                height = str(self._display_heights[display_index].value)

                return fmt.format(display_name, display_serial, width, height)

            return fmt.format('LCOS-SLM', '2018021001', '1920', '1080')

        pzp.param.spinbox(self, 'Wavelength', 575, 450, 1600, visible=False)(None)

        pzp.param.spinbox(self, 'Phase', 2.00, 0.00, 9.99, visible=False, v_step=0.01)(None)

        pzp.param.spinbox(self, 'Contrast', 0, 0, 1023)(None)

        @pzp.param.dropdown(self, 'BMP', '')
        def bmp(self) -> list[str]:
            '''
            Returns BMP from bmp_path.
            '''
            self._bmp_path = r"C:\santec\SLM-200\Hologram sample image"
            return glob.glob(os.path.join(self._bmp_path, '*.bmp'))

        @pzp.param.dropdown(self, 'Data', '')
        def data(self) -> list[str]:
            '''
            Returns data from data_path.
            '''
            self._data_path = r"C:\santec\SLM-200\Files"
            return glob.glob(os.path.join(self._data_path, '*.csv'))

    def define_actions(self):
        '''
        ---Actions---
        Toggle Open :
            Opens in DVI mode and records current tuning.
        Settings :
            Opens popup for interfacing with Display Settings
            and phase_settings.

                Display Settings :
                    Opens popup for interfacing with
                    Display Number, Display Info and Toggle Display.

                        Toggle Display :
                            Toggles display currently given by Display Number.

                Phase Settings :
                    Opens popup for interfacing with
                    Wavelength, Phase and Set Tuning.

                        Set Tuning :
                            Tunes SLM-200 to values given by slm_phase and slm_wavelength;
                            accessible through phase_settings

        Write Contrast :
            Overwrites display with contrast from Contrast.
        Write BMP :
            Overwrites display with bmp from BMP.
        Write Data :
            Overwrites display with data from Data.
        Incr Contrast :
            Increments and displays contrast;
            has shortcut [yet to be assigned].
        Incr BMP :
            Increments bmp in sequence given by BMP;
            has shortcut [yet to be assigned].
        Incr Data :
            Increments unsigned short data array files in sequence
            given by Display Data; has shortcut [yet to be assigned].
        '''

        @pzp.action.define(self, 'Toggle Open')
        def toggle_open(self):
            '''
            Opens/Closes SLM (in DVI mode).
            '''
            if not self.puzzle.debug:
                self._flag = slm.FLAGS_RATE120 # 120Hz model
                self._slm_number = 1 # Only one SLM
                self._slm_mode = 1 # DVI mode
                current_state = self.params['_slm_open'].value

                if not current_state:
                    # Open SLM
                    on = slm.SLM_Ctrl_Open(self._slm_number)

                    if on != slm.SLM_OK:
                        raise SlmError('Could not open SLM.')

                    # DVI mode
                    dvi = slm.SLM_Ctrl_WriteVI(self._slm_number,
                                            self._slm_mode)

                    if dvi != slm.SLM_OK:
                        raise SlmError('DVI mode unsuccessful')

                    print('DVI mode successful.')

                    wavelength = slm.DWORD()
                    phase = slm.DWORD()

                    # Read phase parameters (generally saved from last run)
                    read = slm.SLM_Ctrl_ReadWL(
                        self._slm_number,
                        wavelength,
                        phase
                        )

                    if read != slm.SLM_OK:
                        raise SlmError('Phase read unsuccessful.')

                    # Register phase params
                    self.params['Wavelength'].set_value(wavelength.value)
                    # Machine phase takes format int(100 * float(true_phase))
                    self.params['Phase'].set_value(float(phase.value / 100))
                    print('Phase read successful.')

                    # Register successful open
                    self.params['_slm_open'].set_value(1)
                    print('SLM open successful.')

                else:
                    # Close display
                    if self.params['_display_open'].value:

                        if not self.params['Display Number'].value != '':
                            raise SlmError('Set Display Number')

                        display_number = int(self.params['Display Number'].value)

                        off = slm.SLM_Disp_Close(display_number)

                        if off != slm.SLM_OK:
                            raise SlmError('Display closed unsuccessful.')

                        # Register display closed
                        self.params['_display_open'].set_value(0)
                        print('Display closed successful.')

                    # Close SLM
                    off = slm.SLM_Ctrl_Close(self._slm_number)

                    if off != slm.SLM_OK:
                        raise SlmError('SLM closed unsuccessful.')

                    # Register SLM closed
                    self.params['_slm_open'].set_value(0)
                    print('SLM closed successful.')

        @pzp.action.define(self, 'Settings', 'Right')
        @self._ensure_slm_open
        @self._ensure_slm_ready
        def settings(self):
            '''
            Opens popup for interfacing with 
            Display Settings and Phase Settings.
            '''
            self.open_popup(SlmSettingsPopup)

        @pzp.action.define(self, 'Display Settings', visible=False)
        @self._ensure_slm_open
        @self._ensure_slm_ready
        def display_settings(self):
            '''
            Opens popup for interfacing with
            Display Number, Display Info and Toggle Display.
            '''
            self.open_popup(SlmDisplayPopup)

        @pzp.action.define(self, 'Toggle Display', visible=False)
        @self._ensure_slm_open
        @self._ensure_slm_ready
        @self._ensure_display_number
        def toggle_display(self):
            '''
            Selects display currently given by Display Number.
            '''
            if not self.puzzle.debug:
                current_state = self.params['_display_open'].value
                # Dropdown takes int -> str
                display_number = int(self.params['Display Number'].value)

                if not current_state:
                    # Open display
                    on = slm.SLM_Disp_Open(display_number)

                    if on != slm.SLM_OK:
                        raise SlmError('Display open unsuccessful.')

                    # Register successful open
                    self.params['_display_open'].set_value(1)
                    print('Display open successful.')

                else:
                    # Close display
                    off = slm.SLM_Disp_Close(display_number)

                    if off != slm.SLM_OK:
                        raise SlmError('Display closed unsuccessful.')

                    # Register successful close
                    self.params['_display_open'].set_value(0)
                    print('Display closed successful.')

        @pzp.action.define(self, 'Phase Settings', visible=False)
        @self._ensure_slm_open
        @self._ensure_slm_ready
        @self._ensure_display_open
        def phase_settings(self):
            '''
            Reads hardware phase params and opens
            popup for interfacing with Phase,
            Wavelength and Set Tuning.
            '''
            if not self.puzzle.debug:
                wavelength = slm.DWORD()
                phase = slm.DWORD()

                # Read phase parameters (generally saved from last run)
                read = slm.SLM_Ctrl_ReadWL(
                    self._slm_number,
                    wavelength,
                    phase
                    )

                if read != slm.SLM_OK:
                    raise SlmError('Phase read unsuccessful.')

                # Register phase params
                self.params['Wavelength'].set_value(wavelength.value)
                # Machine phase takes format int(100 * float(true_phase))
                self.params['Phase'].set_value(float(phase.value / 100))
                print('Phase read successful.')

            self.open_popup(SlmPhasePopup)

        @pzp.action.define(self, 'Set Tuning', visible=False)
        @self._ensure_slm_open
        @self._ensure_slm_ready
        @self._ensure_display_open
        def set_tuning(self):
            '''
            Tunes SLM phase params.
            '''
            if not self.puzzle.debug:
                wavelength = self.params['Wavelength'].value
                # Machine phase takes format int(100 * float(true_phase))
                phase = int(self.params['Phase'].value * 100)
                phase_set = slm.SLM_Ctrl_WriteWL(self._slm_number, wavelength, phase)

                if phase_set != slm.SLM_OK:
                    raise SlmError('Phase write unsuccessful.')

                # Register successful phase write
                print('Phase write successful.')

        @pzp.action.define(self, 'Write Contrast')
        @self._ensure_slm_open
        @self._ensure_slm_ready
        @self._ensure_display_open
        def write_contrast(self):
            '''
            Overwrites display with contrast from Contrast.
            '''
            if not self.puzzle.debug:
                # Write Contrast
                display_number = int(self.params['Display Number'].value)
                display = slm.SLM_Disp_GrayScale(
                            display_number,
                            self._flag,
                            self.params['Contrast'].value
                            )

                if display != slm.SLM_OK:
                    raise SlmError('Contrast write unsuccessful.')

                # Register successful contrast write
                print('Contrast write successful.')

        @pzp.action.define(self, 'Incr Contrast')
        @self._ensure_slm_open
        @self._ensure_slm_ready
        @self._ensure_display_open
        def incr_contrast(self):
            '''
            Increments contrast and overwrites display.
            '''
            # Increment Display Number
            self.params['Contrast'].set_value(self.params['Contrast'].value + 1)

            if not self.puzzle.debug:#
                # Write Contrast
                display_number = int(self.params['Display Number'].value)
                display = slm.SLM_Disp_GrayScale(
                            display_number,
                            self._flag,
                            self.params['Contrast'].value
                            )

                if display != slm.SLM_OK:
                    raise SlmError('Contrast increment unsuccessful.')

                # Register successful contrast increment
                print('Contrast increment successful.')

        @pzp.action.define(self, 'Write BMP')
        @self._ensure_slm_open
        @self._ensure_slm_ready
        @self._ensure_display_open
        def write_bmp(self):
            '''
            Overwrites display with bmp from BMP.
            '''

        @pzp.action.define(self, 'Incr BMP')
        @self._ensure_slm_open
        @self._ensure_slm_ready
        @self._ensure_display_open
        def incr_bmp(self):
            '''
            Increments bmp in order given by bmp and overwrites display;
            has shortcut [yet to be assigned]
            '''

        @pzp.action.define(self, 'Write Data')
        @self._ensure_slm_open
        @self._ensure_slm_ready
        @self._ensure_display_open
        def write_data(self):
            '''
            Overwrites display with data from Data.
            '''

        @pzp.action.define(self, 'Incr Data')
        @self._ensure_slm_open
        @self._ensure_slm_ready
        @self._ensure_display_open
        def incr_data(self):
            '''
            Increments data in order given by Data
            and overwrites display.
            '''


class SlmSettingsPopup(pzp.piece.Popup):
    '''
    SlmDVI popup for interfacing with 
    SlmDisplayPopup and SlmPhasePopup.
    '''
    def define_actions(self):
        self.add_child_actions(('Display Settings', 'Phase Settings'))

class SlmDisplayPopup(pzp.piece.Popup):
    '''
    SlmDVI popup for interfacing with 
    slm_display_choose and slm_display_open.
    '''
    def define_params(self):
        self.add_child_params(('Display Number', 'Display Info'))

    def define_actions(self):
        self.add_child_actions(('Toggle Display',))


class SlmPhasePopup(pzp.piece.Popup):
    '''
    SlmDVI popup for interfacing with
    Wavelength and Phase, Set Tuning.
    '''
    def define_params(self):
        self.add_child_params(('Wavelength', 'Phase'))

    def define_actions(self):
        self.add_child_actions(('Set Tuning',))


# Main

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    puzzle = pzp.Puzzle(app, "SLM-200", debug=False)
    puzzle.add_piece("slm_DVI", SlmDVI, 1, 1)
    puzzle.show()
    app.exec()
