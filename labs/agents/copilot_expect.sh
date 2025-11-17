#!/usr/bin/env expect

# Copilot adapter using expect to handle TTY requirements
# Usage: ./copilot_expect.sh <prompt_file>

set timeout 300
log_user 0

# Get environment variables
set session $env(PLANLOOP_SESSION)
set results_dir $env(PLANLOOP_LAB_RESULTS)
set agent_name $env(PLANLOOP_LAB_AGENT_NAME)

# Read prompt from file
set prompt_file [lindex $argv 0]
set fp [open $prompt_file r]
set prompt [read $fp]
close $fp

# Setup output files
set output_dir "$results_dir/$agent_name"
file mkdir $output_dir
set stdout_file [open "$output_dir/${agent_name}_stdout.txt" w]
set trace_file [open "$output_dir/trace.log" w]

puts $trace_file "\[START\] copilot session"
flush $trace_file

# Spawn copilot in interactive mode
spawn copilot --allow-all-tools --allow-all-paths --model gpt-5

# Wait for the prompt
expect {
    "> *" {
        # Send the prompt
        send -- "$prompt\r"
        puts $trace_file "\[PROMPT\] Sent prompt to copilot"
        flush $trace_file
    }
    timeout {
        puts stderr "Timeout waiting for copilot prompt"
        puts $trace_file "\[ERROR\] Timeout waiting for prompt"
        close $trace_file
        close $stdout_file
        exit 1
    }
    eof {
        puts stderr "Copilot exited unexpectedly"
        puts $trace_file "\[ERROR\] Unexpected EOF"
        close $trace_file
        close $stdout_file
        exit 1
    }
}

# Capture all output until copilot returns to prompt or finishes
set done 0
while {!$done} {
    expect {
        -re "(\[^\r\n\]+)" {
            set line $expect_out(1,string)
            puts $stdout_file $line
            flush $stdout_file
            exp_continue
        }
        -re "\n" {
            puts $stdout_file ""
            flush $stdout_file
            exp_continue
        }
        -re "> *Enter.*" {
            # Back at prompt - copilot is done
            puts $trace_file "\[END\] copilot returned to prompt"
            flush $trace_file
            send "exit\r"
            set done 1
        }
        eof {
            puts $trace_file "\[END\] copilot session completed"
            flush $trace_file
            set done 1
        }
        timeout {
            puts $trace_file "\[TIMEOUT\] copilot did not complete in time"
            flush $trace_file
            set done 1
        }
    }
}

close $trace_file
close $stdout_file

# Extract model from output if possible
catch {
    set model_fp [open "$output_dir/${agent_name}_stdout.txt" r]
    set output_content [read $model_fp]
    close $model_fp
    
    if {[regexp {model[:\s]+([a-zA-Z0-9\.\-]+)} $output_content match model]} {
        set model_file [open "$output_dir/model.txt" w]
        puts $model_file $model
        close $model_file
    }
}

wait
set exit_status [lindex [wait] 3]
exit $exit_status
