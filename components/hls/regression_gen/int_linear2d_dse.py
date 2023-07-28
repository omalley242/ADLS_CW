# TODO: Temporary working solution
import sys, os

sys.path.append(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "..",
        "..",
    )
)

from hls.regression_gen.utils import DSE_MODES
from hls.int_arith import int_linear2d_gen
from hls import HLSWriter


def int_linear2d_dse(mode=None, top=None, threads=16):
    assert mode in DSE_MODES, f"Unknown mode {mode}"

    # Small size for debugging only
    # x_widths = [1, 2, 3, 4]
    # x_frac_widths = [1]
    # x_rows = [1, 2, 3, 4]
    # x_cols = [1, 2, 3, 4]
    # w_widths = [1, 2, 3, 4]
    # w_frac_widths = [1]
    # w_rows = [1, 2, 3, 4]

    x_widths = [1, 2, 3, 4, 5, 6, 7, 8]
    x_frac_widths = [1]
    x_rows = [1, 2, 3, 4, 5, 6, 7, 8]
    x_cols = [1, 2, 3, 4]
    w_widths = [1, 2, 3, 4, 5, 6, 7, 8]
    w_frac_widths = [1]
    w_rows = [1, 2, 3, 4]

    # Ignored to reduce complexity
    w_row_depths = [2]
    w_col_depths = [2]
    x_row_depths = [2]
    x_col_depths = [2]
    b_widths = [2]
    b_frac_widths = [2]

    size = (
        len(x_widths)
        * len(x_frac_widths)
        * len(x_rows)
        * len(x_cols)
        * len(w_widths)
        * len(w_frac_widths)
        * len(w_rows)
    )
    print("Exploring linear2d. Design points = {}".format(size))

    i = 0
    commands = [[] for i in range(0, threads)]
    for x_row in x_rows:
        w_col = x_row
        for x_col in x_cols:
            for x_width in x_widths:
                for x_frac_width in x_frac_widths:
                    for w_row in w_rows:
                        for w_width in w_widths:
                            for w_frac_width in w_frac_widths:
                                print(f"Running design {i}/{size}")
                                # Ignored to reduce complexity
                                w_row_depth = 8
                                w_col_depth = 8
                                x_row_depth = 8
                                x_col_depth = 8
                                b_width = 0
                                b_frac_width = 0

                                file_name = f"x{i}_int_linear2d_{x_row}_{x_col}_{x_width}_{x_frac_width}_{w_row}_{w_col}_{w_width}_{w_frac_width}"
                                tcl_path = os.path.join(top, f"{file_name}.tcl")
                                file_path = os.path.join(top, f"{file_name}.cpp")
                                if mode in ["codegen", "all"]:
                                    writer = HLSWriter()
                                    writer = int_linear2d_gen(
                                        writer,
                                        x_width=x_width,
                                        x_frac_width=x_frac_width,
                                        x_row=x_row,
                                        x_col=x_col,
                                        x_row_depth=x_row_depth,
                                        x_col_depth=x_col_depth,
                                        w_width=w_width,
                                        w_frac_width=w_frac_width,
                                        w_row=w_row,
                                        w_col=w_col,
                                        w_row_depth=w_row_depth,
                                        w_col_depth=w_col_depth,
                                        b_width=b_width,
                                        b_frac_width=b_frac_width,
                                    )
                                    writer.emit(file_path)
                                    os.system("clang-format -i {}".format(file_path))
                                    top_name = f"int_linear2d_{writer.op_id-1}"
                                    tcl_buff = f"""
open_project -reset {file_name} 
set_top {top_name}
add_files {{ {file_path} }}
open_solution -reset "solution1"
set_part {{xcu250-figd2104-2L-e}}
create_clock -period 4 -name default
config_bind -effort high
config_compile -pipeline_loops 1
csynth_design
"""
                                    with open(tcl_path, "w", encoding="utf-8") as outf:
                                        outf.write(tcl_buff)
                                    commands[i % threads].append(
                                        f'echo "{i}/{size}"; (cd {top}; vitis_hls {tcl_path})'
                                    )

                                if mode in ["synth", "all"]:
                                    os.system(f"cd {top}; vitis_hls {tcl_path}")

                                i += 1

    if mode in ["codegen", "all"]:
        for i, thread in enumerate(commands):
            f = open(os.path.join(top, f"thread_{i}.sh"), "w")
            for command in thread:
                f.write(command + "\n")
            f.close()

        f = open(os.path.join(top, f"run.sh"), "w")
        f.write(f'echo "int_linear2d" ')
        for i in range(0, len(commands)):
            f.write(f"& bash threads_{i}.sh ")
        f.close()
