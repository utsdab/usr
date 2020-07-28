from collections import OrderedDict

PERSPECTIVE_MODE_LIST = ["Perspective", "Orthographic"]
FIT_MODE_LIST = ["Fill", "Horizontal", "Vertical", "Overscan"]
OVERSCAN_VALUES = [1.00, 1.05, 1.10, 1.30, 1.40, 1.50]
OVERSCAN_VALUES_BAK = ["1.00", "1.05", "1.10", "1.30", "1.40", "1.50"]

FOCAL_LENGTHS = [10.0, 16.0, 18.0, 21.0, 24.0, 35.0, 50.0, 60.0, 70.0, 85.0, 100.0, 150.0,
                 200.0, 300.0]

RESOLUTION_LIST = OrderedDict([("1080p HD (1.77 1920x1080)", (1920, 1080)),
                               ("720p HD (1.77 1280x720)", (1280, 720)),
                               ("540p HD (1.77 960x540)", (960, 540)),
                               ("Ultra HD (1.77 3840x2160)", (3840, 2160)),
                               ("True 4k (1.9 4096x2160)", (4096, 2160)),
                               ("True 2k (1.9 2048x1080)", (2048, 1080)),
                               ("Academy HD (1.85 1920x1038)", (1920, 1038)),
                               ("Cinemascope HD (2.35 1920x817)", (1920, 817)),
                               ("Square 1080 (1 1080x1080)", (1080, 1080)),
                               ("Square 540 (1 540x540)", (540, 540))
                               ])
CLIP_PLANES_LIST = OrderedDict([("Default (.1 to 10000)", (0.1, 10000)),
                                ("Tiny (.009 to 50)", (0.009, 50)),
                                ("Small (.09 to 500)", (0.09, 500)),
                                ("Medium (.9 to 5000)", (0.9, 5000)),
                                ("Large (9 to 50000)", (9, 50000)),
                                ("XLarge (90 to 500000)", (90, 500000))])

SENSOR_SIZE_LIST = OrderedDict([("1/3.2 (iPhone 5)", (4.54, 3.42)),
                                ("Standard 8mm (Camcorder 2000s )", (4.8, 3.5)),
                                ("1/3 (iPhone 5S/6)", (4.80, 3.60)),
                                ("1/2.5 (iPhone XS)", (5.76, 4.29)),
                                ("Super 8mm (Cheap Film 1970s)", (5.79, 4.01)),
                                ("1/2.3 Inch (GoPro Hero 3)", (6.17, 4.55)),
                                ("2/3 Inch Broadcast (Studio, Live Sports)", (8.8, 6.6)),
                                ("Super 16mm (Common Film)", (12.522, 7.417)),
                                ("1 Inch Broadcast (Pocket Cams)", (13.2, 8.6)),
                                ("Micro Four Thirds (Mirrorless Stills)", (17.30, 13.00)),
                                ("35mm 1.85 Projection", (20.955, 11.328)),
                                ("35mm TV Projection", (20.726, 15.545)),
                                ("35mm Anamorphic (2 Lens Squeeze)", (21.946, 18.593)),
                                ("Academy 35mm (1932-50s)", (22, 16)),
                                ("35mm APS-C (Still Canon 60D/7D)", (22.3, 14.9)),
                                ("Super 35mm Full Aperture (Film Default)", (24.892, 18.669)),
                                ("35mm Full Frame (Maya Default, Stills)", (36.0, 24.0)),
                                ("Vista Vision (Special Effects)", (37.719, 25.171)),
                                ("65/70mm Film (Special Effects)", (52.476, 23.012)),
                                ("645 Medium Format", (60, 45)),
                                ("70mm Imax", (70.409, 52.629))])
