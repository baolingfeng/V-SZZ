require 'code-assertions'
require 'logger'
require 'json'
require 'time'

require_relative 'szz-runner'

LOGGER = Logger.new(STDOUT)

INPUT_FILE  = ARGV[0]
MAIN_FOLDER = ARGV[1]
TMP_ROOT    = ARGV[2]
MAX_CORES   = ARGV[3] ? ARGV[3].to_i : nil

if !INPUT_FILE || !MAIN_FOLDER || !TMP_ROOT
    puts "Run with input_filename, folder_with_repos, temporary_directory_root[, max_number_of_cores]"
    exit -1
end

if TMP_ROOT == "/tmp"
    puts "Invalid temporary directory '/tmp'"
end

if MAX_CORES != nil && MAX_CORES <= 0
    puts "The maximum number of cores must be greater than 0"
    exit -1
end

OUTPUT_FILE = File.join(File.expand_path(Dir.getwd), "output_SZZUnleashed_#{Time.now.to_i}.json")

input_data = JSON.parse(File.read(INPUT_FILE))
repositories = input_data.map { |e| e['repo_name'] }.uniq

assert "The elements in the input file must be unique in terms of (repo_name, fix_commit_hash)" do
    mapped = input_data.map { |e| [e['repo_name'], e['fix_commit_hash']]}
    
    mapped.uniq.size == mapped.size
end

SZZUnleashed.setup(MAX_CORES, TMP_ROOT)

output_data = input_data.clone

saver_thread = Thread.start do
    loop do
        sleep 60
        
        File.open(OUTPUT_FILE + ".temp", 'w') do |f|
            f.puts JSON.generate(output_data)
        end
        LOGGER.info("Saved temporary results to #{OUTPUT_FILE}.temp. Next in 60 seconds.")
    end
end

repositories.each do |repository|
    fix_commits = input_data.select { |e| e['repo_name'] == repository }.map do |element|
        fix_commit = FixCommit.new
        fix_commit.hash       = element['fix_commit_hash']
        assert("Invalid input data. The issue must have only one between earliest_issue_date and best_scenario_issue_date") do
            (element['earliest_issue_date'] && !element['best_scenario_issue_date']) || (!element['earliest_issue_date'] && element['best_scenario_issue_date'])
        end
        time_string = element['earliest_issue_date'] ? element['earliest_issue_date'] : element['best_scenario_issue_date']
        fix_commit.issue_date = Time.parse(time_string + " UTC")
        
        fix_commit
    end
    
    repository_path = File.join(MAIN_FOLDER, repository)
    assert("The repository path for #{repository_path} must exist.") { FileTest.exist?(repository_path) }
    
    result = SZZUnleashed.run_pipeline(repository_path, fix_commits)
    
    result.each do |pair|
        correct_element = output_data.select { |e| e['repo_name'] == repository && e['fix_commit_hash'] == pair.fix_hash }.first
        correct_element.assert_nn!
        
        correct_element['inducing_commit_hash'] = [] unless correct_element['inducing_commit_hash']
        correct_element['inducing_commit_hash'] << pair.introducing_hash
        correct_element['inducing_commit_hash'].uniq!
    end
end

saver_thread.kill

output_data.select { |e| e['inducing_commit_hash'] == nil }.each do |no_inducing|
    no_inducing['inducing_commit_hash'] = []
end

File.open(OUTPUT_FILE, 'w') do |f|
    f.puts JSON.generate(output_data)
end

LOGGER.info("Done. Output written at #{OUTPUT_FILE}.")
