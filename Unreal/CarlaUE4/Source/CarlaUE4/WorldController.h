// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma de Barcelona (UAB). This work is licensed under the terms of the MIT license. For a copy, see <https://opensource.org/licenses/MIT>.

#pragma once

#include <string>
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WorldController.generated.h"

UCLASS()
class CARLAUE4_API AWorldController : public AActor
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	AWorldController();

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

	UFUNCTION(BlueprintCallable, CallInEditor)
	void RunPythonScripts(TArray<FString> scriptArray, FString scriptFolder);
};


//==========================================================================

//Class for launching python scripts
class HandlePythonScripts : public FNonAbandonableTask
{
public:
	HandlePythonScripts(FString scriptName, FString folder);
	
	~HandlePythonScripts();

	//required by UE4
	FORCEINLINE TStatId GetStatId() const
	{
		RETURN_QUICK_DECLARE_CYCLE_STAT(HandlePythonScripts, STATGROUP_ThreadPoolAsyncTasks)
	}

	FString PythonScript;
	FString FolderContainingScripts;

	void DoWork();
};