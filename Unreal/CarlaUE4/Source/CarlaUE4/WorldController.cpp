// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB). This work is licensed under the terms of the MIT license. For a copy, see <https://opensource.org/licenses/MIT>.


#include <string>
#include <chrono>
#include <thread>
#include "WorldController.h"
#include <iostream>
#include <thread> 

// Sets default values
AWorldController::AWorldController()
{
 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;

}

// Called when the game starts or when spawned
void AWorldController::BeginPlay()
{
	Super::BeginPlay();
	
}

// Called every frame
void AWorldController::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

}


//==========================================================================

//Star thread for all the given python scripts
void AWorldController::RunPythonScripts(TArray<FString> scriptArray, FString folder)
{
	for (auto& script : scriptArray)
	{
		(new FAutoDeleteAsyncTask<HandlePythonScripts>(script, folder))->StartBackgroundTask();
	}
}

//Assign scriptname
HandlePythonScripts::HandlePythonScripts(FString scriptName, FString folder)
{
	PythonScript = scriptName;
	FolderContainingScripts = folder;
}

//When task is ended
HandlePythonScripts::~HandlePythonScripts()
{
	UE_LOG(LogTemp, Warning, TEXT("Task Finished!"));
}

//Launch script
void HandlePythonScripts::DoWork()
{
	//FString script = FolderContainingScripts + PythonScript;
	//char* result = TCHAR_TO_ANSI(*script);
	//system(result);
	FString openFolder = "cd " + FolderContainingScripts;
	FString launchScript = "python " + PythonScript;
	FString finalCommand = openFolder + " && " + launchScript;
	char* command = TCHAR_TO_ANSI(*finalCommand);
	system(command);

	/*using namespace std::this_thread;     // sleep_for, sleep_until
	using namespace std::chrono_literals; // ns, us, ms, s, h, etc.
	using std::chrono::system_clock;

	sleep_for(10000ns);*/
}
