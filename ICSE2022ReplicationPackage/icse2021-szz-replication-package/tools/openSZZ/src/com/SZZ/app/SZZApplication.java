package com.SZZ.app;

import com.SZZ.jiraAnalyser.Application;
import com.SZZ.jiraAnalyser.git.Git;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.net.MalformedURLException;
import java.nio.file.Files;
import java.util.LinkedList;
import java.util.List;

public class SZZApplication {

	/* Get actual class name to be printed on */
	
	private static String jiraAPI = "/jira/sr/jira.issueviews:searchrequest-xml/temp/SearchRequest.xml";

	public static void main(String[] args) {
//		args = new String[7];
//		args[0] = "-all";
//		args[1] = "https://github.com/jwang36/edk2.git"; // "https://github.com/apache/commons-bcel.git";
//		args[2] = "https://issues.apache.org/jira/projects/BCEL";
//		args[3] = "jwang36/edk2";//"BCEL";
//		args[4] = "jwang36_edk2.txt";



		if (args.length == 0) {
			System.out.println("Welcome to SZZ Calculation script.");
			System.out.println("Here a guide how to use the script");
			System.out.println("szz.jar -all githubUrl, jiraUrl, jiraKey => all steps together");
		} else {
			switch (args[0]) {
			case "-all":
				Git git;
//				try {
//					String[] array = args[2].split("/jira/projects/");
//					String projectName = args[3];
//					String jiraUrl = array[0] + jiraAPI;
//					JiraRetriever jr1 = new JiraRetriever(jiraUrl, projectName);
//					jr1.printIssues();
//
//				} catch (Exception e) {
//					break;
//				}

				List<String> ourHashes = new LinkedList<>();
				String projectFileName = args[4];
				try (BufferedReader br = new BufferedReader(new FileReader(projectFileName))) {
					String line;
					while ((line = br.readLine()) != null) {
						ourHashes.add(line);
					}
				}catch (IOException e) {
					e.printStackTrace();
				}

				try {
					Application a = new Application();
					a.mineData(args[1], args[2].replace("{0}", args[3]), args[3], args[3], ourHashes);
				} catch (MalformedURLException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				} catch (Exception e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
				//clean(args[3]);
				break;
			default:
				System.out.println("Commands are not in the right form! Please retry!");
				break;

			}
		}

	}

	private static void clean(String jiraKey) {
		for (File fileEntry : new File(".").listFiles()) {
			if (fileEntry.getName().toLowerCase().contains(jiraKey.toLowerCase())) {
				if (!fileEntry.getName().contains("Commit")) {
					try {
						if (fileEntry.isFile())
							Files.deleteIfExists(fileEntry.toPath());
						else
							deleteDir(fileEntry);
					} catch (IOException e) {
						// TODO Auto-generated catch block
						e.printStackTrace();
					}
				}
			}
		}
	}

	private static void deleteDir(File file) {
		File[] contents = file.listFiles();
		if (contents != null) {
			for (File f : contents) {
				deleteDir(f);
			}
		}
		file.delete();
	}
}
