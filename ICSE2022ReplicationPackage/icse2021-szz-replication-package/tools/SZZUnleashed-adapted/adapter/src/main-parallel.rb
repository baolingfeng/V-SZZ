require 'code-assertions'
require 'json'

INPUT_FILE  = ARGV[0]
MAIN_FOLDER = ARGV[1] ? File.expand_path(ARGV[1]) : nil
NUM_THREADS = ARGV[2].to_i
MAX_CORES   = ARGV[3] ? ARGV[3].to_i : 1

PATH_TO_MAIN = File.join(File.dirname(File.expand_path(__FILE__)), "main.rb")

WORKING_FOLDER = File.expand_path("parallel-szzunleashed")
LOG_FOLDER     = File.join(WORKING_FOLDER, "logs")
INPUT_FOLDER   = File.join(WORKING_FOLDER, "input")
OUTPUT_FOLDER  = File.join(WORKING_FOLDER, "output")
TMP_FOLDER     = File.join(WORKING_FOLDER, "tmp")
assert("The directory #{WORKING_FOLDER} should not exist. Delete it if this is a re-run.") { !FileTest.exist?(WORKING_FOLDER) }

if !INPUT_FILE || !MAIN_FOLDER || NUM_THREADS == 0
    puts "Run with input_filename, folder_with_repos, number_of_threads[, max_number_of_cores_per_thread=1]"
    exit -1
end

class Array
    def make_partition(number)
        group_size = size / number
        leftovers = size % number

        groups = []
        start = 0
        number.times do |index|
            length = group_size + (leftovers > 0 && leftovers > index ? 1 : 0)
            groups << slice(start, length)
            start += length
        end

        return groups
    end

    def stratified_sample(n)
        self.stratify(n).map { |stratum| stratum.first }
    end
    
    def stratify(n)
        self.sort_by { |e| yield(e) }.make_partition(n).map { |stratum| stratum.shuffle }
    end
    
    def mean
        self.sum.to_f / self.size
    end
end

 
assert("The number of threads must be > 0") { NUM_THREADS > 0 }

input_data = JSON.parse(File.read(INPUT_FILE))

repositories = input_data.map { |e| e['repo_name'] }.uniq

`mkdir -p "#{INPUT_FOLDER}"`
`mkdir -p "#{OUTPUT_FOLDER}"`
`mkdir -p "#{LOG_FOLDER}"`
slot_input_filenames = []
repositories.shuffle.make_partition(NUM_THREADS).each_with_index do |repos, i|
    slot_elements = input_data.select { |e| repos.include?(e['repo_name']) }
    
    partial_json = JSON.generate(slot_elements)
    
    partial_filename = File.join(INPUT_FOLDER, File.basename(INPUT_FILE)).sub(".json", ".#{i}.json")
    File.open(partial_filename, 'w') do |f|
        f.write partial_json
    end
    slot_input_filenames << partial_filename
end


Dir.chdir(OUTPUT_FOLDER) do
    threads = []
    slot_input_filenames.each do |input_filename|
        threads << Thread.start(input_filename) do |input_filename|
            puts "Started thread for #{input_filename}"
            `ruby "#{PATH_TO_MAIN}" "#{input_filename}" "#{MAIN_FOLDER}" "#{TMP_FOLDER}" #{MAX_CORES} > "#{LOG_FOLDER}/#{File.basename(input_filename)}.log" 2> "#{LOG_FOLDER}/#{File.basename(input_filename)}.err.log"`
            puts "Done with #{input_filename}: #{threads.count { |t| t.alive? } - 1} threads still running"
        end
        sleep 2
    end
    puts "All the threads started. Waiting for them..."
    threads.each { |t| t.join }
end
puts "Threads completed. Joining the results..."

result = []
Dir.glob(File.join(OUTPUT_FOLDER, "*.json")).each do |output_filename|
    json = JSON.parse(File.read(output_filename))
    result += json
end

if result.size != input_data.size
    warn "CAREFUL! result size and input size seem to differ (#{result.size} vs #{input_data.size}). Please, double-check."
end

out_filename = File.basename(Dir.glob(File.join(OUTPUT_FOLDER, "*.json")).max)
File.open(out_filename, 'w') do |f|
    f.write JSON.generate(result)
end
puts "All done."
